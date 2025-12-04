import { useNavigate, Link } from 'react-router-dom';
import { LoginForm } from '../components/Auth/LoginForm';

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-indigo-600">Lynex</h1>
          <p className="text-gray-500 mt-2">Sign in to your account</p>
        </div>

        <LoginForm />

        <p className="text-center mt-6 text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/signup" className="text-indigo-600 hover:text-indigo-500 font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
