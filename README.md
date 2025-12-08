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
- **Static Deployment**: Runs entirely client-side on S3

## Getting Started

### Prerequisites

- Node.js 18+
- AWS S3 bucket (for static hosting and admin token)
- Google OAuth application (for user authentication)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
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

## API Endpoints

### Public Endpoints
- `GET /api/objects/[name]?token=[token]` - Access object by name and token

### Admin Endpoints (require admin authentication)
- `POST /api/objects/create` - Create new object
- `GET /api/admin/objects` - List all objects with pagination and filtering
- `GET /api/admin/cleanup` - Get cleanup statistics
- `POST /api/admin/cleanup` - Trigger manual cleanup

### Authentication Endpoints
- `/api/auth/signin` - Google OAuth sign-in
- `/api/auth/signout` - Sign out
- `/api/auth/session` - Get current session

## Architecture

- **Frontend**: Next.js with TypeScript and Tailwind CSS
- **Backend**: Next.js API routes
- **Database**: PostgreSQL with Prisma ORM
- **Authentication**: NextAuth.js with Google OAuth
- **Storage**: AWS S3
- **Scheduling**: Node-cron for automated cleanup

## Database Schema

- **Users**: Google OAuth user data and admin privileges
- **StorageObjects**: Object metadata, tokens, and TTL
- **ObjectAnalytics**: Hit tracking and usage statistics
- **NextAuth tables**: Session and account management

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run db:generate` - Generate Prisma client
- `npm run db:migrate` - Run database migrations
- `npm run db:push` - Push schema to database
- `npm run db:studio` - Open Prisma Studio

### Project Structure

```
src/
├── components/          # Reusable React components
├── lib/                # Utility libraries (auth, database, S3, etc.)
├── pages/              # Next.js pages and API routes
│   ├── api/            # API endpoints
│   ├── admin/          # Admin dashboard pages
│   └── onboard.tsx     # Public onboarding page
├── styles/             # CSS styles
└── types/              # TypeScript type definitions
```

## Security Features

- Google OAuth authentication for admin access
- Unique token generation for object access
- TTL-based automatic expiration
- Admin-only access to sensitive operations
- Secure S3 integration

## License

This project is licensed under the MIT License.# trufo
