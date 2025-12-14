const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const { DynamoDBDocumentClient, GetCommand, PutCommand, QueryCommand, DeleteCommand, ScanCommand } = require("@aws-sdk/lib-dynamodb");
const crypto = require('crypto');

// AWS_REGION is automatically available in Lambda environment
const client = new DynamoDBClient({ region: process.env.AWS_REGION });
const docClient = DynamoDBDocumentClient.from(client);

const TABLE_NAME = process.env.DYNAMODB_TABLE_NAME || 'trufo-objects';

// Encryption key (in production, use AWS KMS or environment variable)
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'default-key-change-in-production-32b';
const ALGORITHM = 'aes-256-cbc';

// Ensure encryption key is proper length for AES-256
function getEncryptionKey() {
  const key = Buffer.from(ENCRYPTION_KEY, 'utf8');
  if (key.length === 32) return key;
  // Pad or truncate to 32 bytes
  const paddedKey = Buffer.alloc(32);
  key.copy(paddedKey, 0, 0, Math.min(key.length, 32));
  return paddedKey;
}

// Encrypt content
function encryptContent(text) {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv(ALGORITHM, getEncryptionKey(), iv);
  let encrypted = cipher.update(JSON.stringify(text), 'utf8', 'hex');
  encrypted += cipher.final('hex');
  return `${iv.toString('hex')}:${encrypted}`;
}

// Decrypt content
function decryptContent(encryptedText) {
  try {
    const [ivHex, encrypted] = encryptedText.split(':');
    if (!ivHex || !encrypted) {
      // Handle backwards compatibility for non-encrypted data
      return JSON.parse(encryptedText);
    }
    const iv = Buffer.from(ivHex, 'hex');
    const decipher = crypto.createDecipheriv(ALGORITHM, getEncryptionKey(), iv);
    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    return JSON.parse(decrypted);
  } catch (error) {
    console.error('Decryption failed:', error);
    return encryptedText; // Return as-is if decryption fails (backwards compatibility)
  }
}

// Generate TOTP secret
function generateTOTPSecret() {
  return crypto.randomBytes(20).toString('base32');
}

// Verify TOTP token
function verifyTOTPToken(secret, token) {
  if (!secret || !token) return false;

  // TOTP algorithm - generates 6-digit code based on time window
  const timeWindow = Math.floor(Date.now() / 30000); // 30-second window

  // Generate codes for current and previous/next windows (allows for clock drift)
  for (let i = -1; i <= 1; i++) {
    const windowTime = timeWindow + i;
    const hmac = crypto.createHmac('sha1', Buffer.from(secret, 'base32'));
    hmac.update(Buffer.from(windowTime.toString(16).padStart(16, '0'), 'hex'));
    const hash = hmac.digest();

    // Extract dynamic binary code
    const offset = hash[hash.length - 1] & 0xf;
    const code = (
      ((hash[offset] & 0x7f) << 24) |
      ((hash[offset + 1] & 0xff) << 16) |
      ((hash[offset + 2] & 0xff) << 8) |
      (hash[offset + 3] & 0xff)
    ) % 1000000;

    if (code.toString().padStart(6, '0') === token) {
      return true;
    }
  }

  return false;
}

// Response helper (AWS Function URLs handle CORS automatically)
const response = (statusCode, body, additionalHeaders = {}) => ({
  statusCode,
  headers: {
    'Content-Type': 'application/json',
    ...additionalHeaders
  },
  body: JSON.stringify(body)
});

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));

  // Handle preflight OPTIONS request
  if (event.requestContext?.http?.method === 'OPTIONS') {
    return response(200, { message: 'OK' });
  }

  // Block ALL direct Lambda access - only allow CloudFront with secret header
  const CF_SECRET = process.env.CLOUDFRONT_SECRET || 'trufo-cf-secret-2025-secure-key-32ch';
  const cfSecretHeader = event.headers?.['x-cf-secret'] || event.headers?.['X-CF-Secret'];

  if (cfSecretHeader !== CF_SECRET) {
    console.log('Blocked direct Lambda access - missing or invalid CloudFront secret');
    return response(403, { error: 'Direct access forbidden - use CloudFront only' });
  }

  // Function URL vs API Gateway event compatibility
  const method = event.requestContext?.http?.method || event.httpMethod;
  const pathname = event.requestContext?.http?.path || event.path || event.rawPath;

  // Log request for debugging
  console.log(`${method} ${pathname}`);
  console.log('Headers:', JSON.stringify(event.headers, null, 2));

  try {
    // Parse request body if present
    let body = {};
    if (event.body) {
      body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;
    }

    console.log('Request body:', JSON.stringify(body, null, 2));

    // Route requests
    switch (`${method} ${pathname}`) {

      // Create object
      case 'POST /objects':
        return await createObject(body);

      // Get object by token and name
      case 'GET /objects':
        const { name, token, totpCode } = event.queryStringParameters || {};
        return await getObject(name, token, totpCode);

      // Get object by token only
      case 'GET /object':
        const { token: objToken, totpCode: objTotpCode } = event.queryStringParameters || {};
        return await getObjectByToken(objToken, objTotpCode);

      // Get user's objects
      case 'GET /user-objects':
        const { email } = event.queryStringParameters || {};
        return await getUserObjects(email);

      // Update object
      case 'PUT /objects':
        return await updateObject(body);

      // Delete object
      case 'DELETE /objects':
        const { id } = event.queryStringParameters || {};
        return await deleteObject(id);

      // Toggle boolean object
      case 'POST /toggle':
        const { name: toggleName, token: toggleToken } = body;
        return await toggleBooleanObject(toggleName, toggleToken);


      default:
        return response(404, { error: 'Not found' });
    }

  } catch (error) {
    console.error('Error:', error);
    return response(500, { error: 'Internal server error', details: error.message });
  }
};

// Create a new object
async function createObject(data) {
  console.log('Creating object with data:', JSON.stringify(data, null, 2));

  const { name, type, content, ttlHours, ownerEmail, ownerName, oneTimeAccess, enableMFA } = data;

  if (!name || !type || content === undefined || content === null || ttlHours === undefined || ttlHours === null) {
    return response(400, { error: 'Missing required fields: name, type, content, ttlHours' });
  }

  // Generate missing fields
  const id = `obj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const token = crypto.randomBytes(16).toString('hex'); // 32-character hex token
  const ttl = Date.now() + (parseFloat(ttlHours) * 60 * 60 * 1000); // Convert hours to milliseconds

  // Encrypt content for security
  const encryptedContent = encryptContent(content);

  const item = {
    id,
    name,
    type,
    content: encryptedContent,
    ttl,
    token,
    ownerEmail: ownerEmail || 'anonymous',
    ownerName: ownerName || 'Anonymous User',
    hitCount: 0,
    createdAt: Date.now(),
    lastHit: null,
    oneTimeAccess: oneTimeAccess || false,
    totpSecret: enableMFA ? generateTOTPSecret() : null
  };

  console.log('Inserting item to DynamoDB:', JSON.stringify(item, null, 2));

  try {
    const command = new PutCommand({
      TableName: TABLE_NAME,
      Item: item
    });

    await docClient.send(command);
    console.log('Item inserted successfully');
    return response(201, { success: true, object: item });
  } catch (error) {
    console.error('Error inserting item to DynamoDB:', error);
    return response(500, { error: 'Failed to create object', details: error.message });
  }
}

// Get object by name and token
async function getObject(name, token, totpCode) {
  if (!name || !token) {
    return response(400, { error: 'Name and token are required' });
  }

  // Query by name (GSI) and filter by token
  const command = new QueryCommand({
    TableName: TABLE_NAME,
    IndexName: 'name-index',
    KeyConditionExpression: '#name = :name',
    ExpressionAttributeNames: { '#name': 'name' },
    ExpressionAttributeValues: { ':name': name }
  });

  const result = await docClient.send(command);
  const object = result.Items.find(item => item.token === token);

  if (!object) {
    return response(404, { error: 'Object not found or invalid token' });
  }

  // Check if expired - DELETE expired objects
  if (object.ttl <= Date.now()) {
    // Delete expired object
    const deleteCommand = new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { id: object.id }
    });
    await docClient.send(deleteCommand);

    return response(410, { error: 'Object has expired and has been deleted' });
  }

  // Check TOTP MFA if enabled
  if (object.totpSecret) {
    if (!totpCode) {
      return response(403, {
        error: 'TOTP verification required',
        requiresTOTP: true,
        totpQR: object.hitCount === 0 ? `otpauth://totp/Trufo:${object.name}?secret=${object.totpSecret}&issuer=Trufo` : undefined
      });
    }

    if (!verifyTOTPToken(object.totpSecret, totpCode)) {
      return response(403, { error: 'Invalid TOTP code' });
    }
  }

  // Update hit count
  const updateCommand = new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      ...object,
      hitCount: object.hitCount + 1,
      lastHit: Date.now()
    }
  });

  await docClient.send(updateCommand);

  // Decrypt content
  const decryptedContent = decryptContent(object.content);

  // Handle one-time access - DELETE after reading
  if (object.oneTimeAccess) {
    const deleteCommand = new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { id: object.id }
    });
    await docClient.send(deleteCommand);
  }

  // Return content based on type
  let responseContent;
  if (object.type === 'toggle') {
    responseContent = decryptedContent; // Return current value first

    // Only toggle if not one-time access (since object is deleted)
    if (!object.oneTimeAccess) {
      // Update the object with toggled content AFTER reading
      const toggledContent = !decryptedContent;
      const encryptedToggled = encryptContent(toggledContent);

      const toggleUpdateCommand = new PutCommand({
        TableName: TABLE_NAME,
        Item: {
          ...object,
          content: encryptedToggled, // Store encrypted toggled value
          hitCount: object.hitCount + 1,
          lastHit: Date.now()
        }
      });
      await docClient.send(toggleUpdateCommand);
    }
  } else {
    // For 'string' and 'boolean' types, just return the content
    responseContent = decryptedContent;
  }

  const responseData = {
    content: responseContent,
    hits: object.hitCount + 1
  };


  return response(200, responseData);
}

// Get object by token only (simpler access)
async function getObjectByToken(token, totpCode) {
  if (!token) {
    return response(400, { error: 'Token is required' });
  }

  // Query by token (use scan since we don't have a token index)
  const command = new ScanCommand({
    TableName: TABLE_NAME,
    FilterExpression: '#token = :token',
    ExpressionAttributeNames: { '#token': 'token' },
    ExpressionAttributeValues: { ':token': token }
  });

  const result = await docClient.send(command);
  const object = result.Items && result.Items[0];

  if (!object) {
    return response(404, { error: 'Object not found or invalid token' });
  }

  // Check if expired - DELETE expired objects
  if (object.ttl <= Date.now()) {
    const deleteCommand = new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { id: object.id }
    });
    await docClient.send(deleteCommand);
    return response(410, { error: 'Object has expired and has been deleted' });
  }

  // Check TOTP MFA if enabled
  if (object.totpSecret) {
    if (!totpCode) {
      return response(403, {
        error: 'TOTP verification required',
        requiresTOTP: true,
        totpQR: object.hitCount === 0 ? `otpauth://totp/Trufo:${object.name}?secret=${object.totpSecret}&issuer=Trufo` : undefined
      });
    }

    if (!verifyTOTPToken(object.totpSecret, totpCode)) {
      return response(403, { error: 'Invalid TOTP code' });
    }
  }

  // Update hit count
  const updateCommand = new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      ...object,
      hitCount: object.hitCount + 1,
      lastHit: Date.now()
    }
  });
  await docClient.send(updateCommand);

  // Decrypt content
  const decryptedContent = decryptContent(object.content);

  // Handle one-time access - DELETE after reading
  if (object.oneTimeAccess) {
    const deleteCommand = new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { id: object.id }
    });
    await docClient.send(deleteCommand);
  }

  // Return content based on type
  let responseContent;
  if (object.type === 'toggle') {
    responseContent = decryptedContent; // Return current value first

    // Only toggle if not one-time access (since object is deleted)
    if (!object.oneTimeAccess) {
      // Update the object with toggled content AFTER reading
      const toggledContent = !decryptedContent;
      const encryptedToggled = encryptContent(toggledContent);

      const toggleUpdateCommand = new PutCommand({
        TableName: TABLE_NAME,
        Item: {
          ...object,
          content: encryptedToggled, // Store encrypted toggled value
          hitCount: object.hitCount + 1,
          lastHit: Date.now()
        }
      });
      await docClient.send(toggleUpdateCommand);
    }
  } else {
    // For 'string' and 'boolean' types, just return the content
    responseContent = decryptedContent;
  }

  const responseData = {
    name: object.name,
    type: object.type,
    content: responseContent,
    hits: object.hitCount + 1
  };

  return response(200, responseData);
}

// Get all objects for a user
async function getUserObjects(email) {
  if (!email) {
    return response(400, { error: 'Email is required' });
  }

  const command = new QueryCommand({
    TableName: TABLE_NAME,
    IndexName: 'owner-index',
    KeyConditionExpression: 'ownerEmail = :email',
    ExpressionAttributeValues: { ':email': email }
  });

  const result = await docClient.send(command);
  return response(200, { objects: result.Items || [] });
}

// Update an object
async function updateObject(data) {
  const { id, updates } = data;

  if (!id) {
    return response(400, { error: 'Object ID is required' });
  }

  // Get current object
  const getCommand = new GetCommand({
    TableName: TABLE_NAME,
    Key: { id }
  });

  const currentResult = await docClient.send(getCommand);
  if (!currentResult.Item) {
    return response(404, { error: 'Object not found' });
  }

  // Update object
  const updatedItem = { ...currentResult.Item, ...updates };
  const putCommand = new PutCommand({
    TableName: TABLE_NAME,
    Item: updatedItem
  });

  await docClient.send(putCommand);
  return response(200, { success: true, object: updatedItem });
}

// Delete an object
async function deleteObject(id) {
  if (!id) {
    return response(400, { error: 'Object ID is required' });
  }

  const command = new DeleteCommand({
    TableName: TABLE_NAME,
    Key: { id }
  });

  await docClient.send(command);
  return response(200, { success: true });
}

// Toggle boolean object
async function toggleBooleanObject(name, token) {
  if (!name || !token) {
    return response(400, { error: 'Name and token are required' });
  }

  // Query by name and filter by token
  const command = new QueryCommand({
    TableName: TABLE_NAME,
    IndexName: 'name-index',
    KeyConditionExpression: '#name = :name',
    ExpressionAttributeNames: { '#name': 'name' },
    ExpressionAttributeValues: { ':name': name }
  });

  const result = await docClient.send(command);
  const object = result.Items.find(item => item.token === token);

  if (!object) {
    return response(404, { error: 'Object not found or invalid token' });
  }

  // Check if expired
  if (object.ttl <= Date.now()) {
    const deleteCommand = new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { id: object.id }
    });
    await docClient.send(deleteCommand);
    return response(410, { error: 'Object has expired and has been deleted' });
  }

  // Only allow toggle for boolean objects
  if (object.type !== 'boolean') {
    return response(400, { error: 'Toggle is only supported for boolean objects' });
  }

  // Decrypt current content
  const currentContent = decryptContent(object.content);
  const toggledContent = !currentContent;

  // Encrypt new content
  const encryptedContent = encryptContent(toggledContent);

  // Update object with toggled content
  const updateCommand = new PutCommand({
    TableName: TABLE_NAME,
    Item: {
      ...object,
      content: encryptedContent,
      hitCount: object.hitCount + 1,
      lastHit: Date.now()
    }
  });

  await docClient.send(updateCommand);

  return response(200, {
    content: toggledContent,
    hits: object.hitCount + 1
  });
}

