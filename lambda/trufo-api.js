const { DynamoDBClient } = require("@aws-sdk/client-dynamodb");
const { DynamoDBDocumentClient, GetCommand, PutCommand, QueryCommand, DeleteCommand, ScanCommand } = require("@aws-sdk/lib-dynamodb");

// AWS_REGION is automatically available in Lambda environment
const client = new DynamoDBClient({ region: process.env.AWS_REGION });
const docClient = DynamoDBDocumentClient.from(client);

const TABLE_NAME = process.env.DYNAMODB_TABLE_NAME || 'trufo-objects';

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
        const { name, token } = event.queryStringParameters || {};
        return await getObject(name, token);

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

      // Admin: Get all objects
      case 'GET /admin/objects':
        const { adminToken } = event.queryStringParameters || {};
        return await adminGetAllObjects(adminToken);

      // Admin: Cleanup expired
      case 'POST /admin/cleanup':
        const { adminToken: cleanupToken } = body;
        return await adminCleanup(cleanupToken);

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

  const { name, type, content, ttlHours, ownerEmail, ownerName } = data;

  if (!name || !type || content === undefined || !ttlHours) {
    return response(400, { error: 'Missing required fields: name, type, content, ttlHours' });
  }

  // Generate missing fields
  const id = `obj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const token = Math.random().toString(36).substr(2, 12);
  const ttl = Date.now() + (parseInt(ttlHours) * 60 * 60 * 1000); // Convert hours to milliseconds

  const item = {
    id,
    name,
    type,
    content,
    ttl,
    token,
    ownerEmail: ownerEmail || 'anonymous',
    ownerName: ownerName || 'Anonymous User',
    hitCount: 0,
    createdAt: Date.now(),
    lastHit: null
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
async function getObject(name, token) {
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

  // Check if expired
  if (object.ttl <= Date.now()) {
    return response(410, { error: 'Object has expired' });
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

  // Return content based on type
  let responseContent;
  if (object.type === 'toggle') {
    responseContent = object.content; // Return current value first
    // Update the object with toggled content AFTER reading
    const toggleUpdateCommand = new PutCommand({
      TableName: TABLE_NAME,
      Item: {
        ...object,
        content: !object.content, // Store the toggled value
        hitCount: object.hitCount + 1,
        lastHit: Date.now()
      }
    });
    await docClient.send(toggleUpdateCommand);
  } else {
    responseContent = object.content;
  }

  return response(200, { content: responseContent, hits: object.hitCount + 1 });
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

// Admin: Get all objects
async function adminGetAllObjects(adminToken) {
  // Verify admin token (you can implement S3 check here or use env var)
  const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'your-admin-token';

  if (adminToken !== ADMIN_TOKEN) {
    return response(403, { error: 'Invalid admin token' });
  }

  const command = new ScanCommand({
    TableName: TABLE_NAME
  });

  const result = await docClient.send(command);
  return response(200, { objects: result.Items || [] });
}

// Admin: Cleanup expired objects
async function adminCleanup(adminToken) {
  const ADMIN_TOKEN = process.env.ADMIN_TOKEN || 'your-admin-token';

  if (adminToken !== ADMIN_TOKEN) {
    return response(403, { error: 'Invalid admin token' });
  }

  const now = Date.now();

  // Get all objects
  const scanCommand = new ScanCommand({
    TableName: TABLE_NAME
  });

  const result = await docClient.send(scanCommand);
  const allObjects = result.Items || [];

  // Find expired objects
  const expiredObjects = allObjects.filter(obj => obj.ttl <= now);

  // Delete expired objects
  for (const obj of expiredObjects) {
    const deleteCommand = new DeleteCommand({
      TableName: TABLE_NAME,
      Key: { id: obj.id }
    });
    await docClient.send(deleteCommand);
  }

  return response(200, {
    success: true,
    deletedCount: expiredObjects.length,
    message: `Cleaned up ${expiredObjects.length} expired objects`
  });
}