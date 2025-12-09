# Trufo - Static Token-Based Object Storage

A secure, token-based object storage system with Google OAuth authentication, user isolation, and S3-based admin management.

## Features

- **Token-Based Access**: Secure object access using unique tokens
- **Google OAuth Authentication**: User sign-in with minimal permissions
- **User Isolation**: Users can only see and manage their own objects
- **Object Types**: String objects (return content) and Toggle objects (flip true/false on access)
- **TTL Management**: Automatic expiration and cleanup of objects
- **Analytics Tracking**: Hit count and access time tracking
- **Admin Dashboard**: S3 token-based admin access to view all objects
- **Static Deployment**: Runs entirely client-side with S3 + CloudFront

## Getting Started

### Prerequisites

- Node.js 18+
- AWS S3 bucket (for data storage and admin token)
- AWS CloudFront distribution (recommended for HTTPS and global CDN)
- Google OAuth application (for user authentication)

### Installation

1. Clone the repository:
```bash
git clone git@github.com:maimon33/trufo.git
cd trufo
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Fill in the required environment variables:

```env
# Google OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id

# S3 Configuration for Admin Token Access
VITE_S3_BUCKET_URL=https://your-bucket.s3.amazonaws.com
```

4. Set up Google OAuth:

   **Step 1: Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "Select a project" → "New Project"
   - Name your project (e.g., "Trufo Auth")
   - Click "Create"

   **Step 2: Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" (unless you have Google Workspace)
   - Fill required fields:
     - App name: "Trufo"
     - User support email: Your email
     - Developer contact: Your email
   - Click "Save and Continue"
   - Skip scopes (default is fine)
   - Add test users: Add your email address
   - Click "Save and Continue"

   **Step 3: Create OAuth Client ID**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Web application"
   - Name: "Trufo Web Client"
   - **Authorized JavaScript origins**:
     - For local dev: `http://localhost:3000`
     - For production: `https://your-domain.com`
   - **Authorized redirect URIs**:
     - For local dev: `http://localhost:3000`
     - For production: `https://your-domain.com`
   - Click "Create"
   - Copy the Client ID (looks like: `123456789-abc123.apps.googleusercontent.com`)

5. Set up S3 Admin Token (optional):
   - Create a file at `s3://your-bucket/admin/admin-token.txt`
   - Put a long, random string as the admin token
   - This enables admin access to view all objects

6. **Development Admin Access**:
   - For local development, use admin token: `root`
   - This bypasses S3 token verification in dev mode

7. Start the development server:
```bash
npm run dev
```

## Usage

### For Users

1. **Sign In**: Use Google OAuth to sign in (requires minimal permissions)
2. **Create Objects**: Visit `/create` to create string or toggle objects with TTL
3. **Manage Objects**: Visit `/manage` to view and edit your objects
4. **Access Objects**: Use the access URL with your token:
   ```
   GET /access/[object-name]?token=[your-token]
   ```

### For Admins

1. **Admin Access**: Visit `/admin` and enter the admin token from S3
2. **View All Objects**: See objects from all users with owner information
3. **Manage Any Object**: Edit or delete objects from any user
4. **Analytics**: View system-wide hit counts and usage patterns

## Required GitHub Secrets

For automated deployment, configure these secrets in your GitHub repository:

**AWS Deployment:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `S3_BUCKET` - S3 bucket name
- `CLOUDFRONT_DISTRIBUTION_ID` - CloudFront distribution ID (optional)

**Application Configuration:**
- `VITE_GOOGLE_CLIENT_ID` - Google OAuth client ID
- `VITE_S3_BUCKET_URL` - S3 bucket URL for data access

## API Endpoints

### Object Access
- `GET /access/[name]?token=[token]` - Access object by name and token

### Admin Routes
- `/admin` - Admin dashboard (requires admin token)
- `/create` - Create new objects (requires Google sign-in)
- `/manage` - Manage user's objects (requires Google sign-in)

## Deployment Options

### Option 1: S3 + CloudFront (Recommended)

**Pros:**
- ✅ Global CDN with fast loading
- ✅ Free HTTPS with AWS Certificate Manager
- ✅ Custom domain support
- ✅ Integrated with AWS ecosystem
- ✅ Cost-effective for high traffic

**Setup:**
1. Create S3 bucket for storage
2. Create CloudFront distribution pointing to S3
3. Configure custom domain with Route 53
4. Deploy using GitHub Actions

### Option 2: Netlify

**Pros:**
- ✅ Simple setup and deployment
- ✅ Free HTTPS and custom domains
- ✅ Excellent SPA routing support
- ✅ Built-in CI/CD from GitHub
- ✅ Free tier for low traffic

**Setup:**
1. Connect GitHub repo to Netlify
2. Configure environment variables
3. Deploy automatically on push

## Architecture

- **Frontend**: React with TypeScript, Vite, and Tailwind CSS
- **Database**: JSON storage in S3 (client-side)
- **Authentication**: Google OAuth with Identity Services
- **Hosting**: S3 + CloudFront or Netlify
- **Admin Access**: S3-based token authentication

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint (if configured)

### Project Structure

```
src/
├── components/          # Reusable React components
├── lib/                # Utility libraries (auth, storage, admin)
├── pages/              # Application pages/routes
├── types/              # TypeScript type definitions
└── main.tsx            # Application entry point
```

## Security Features

- Google OAuth authentication for admin access
- Unique token generation for object access
- TTL-based automatic expiration
- Admin-only access to sensitive operations
- Secure S3 integration

## License

This project is licensed under the MIT License.# trufo
