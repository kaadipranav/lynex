import { useNavigate, Link } from 'react-router-dom';
import { SignupForm } from '../components/Auth/SignupForm';

export default function SignupPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-indigo-600">WatchLLM</h1>
          <p className="text-gray-500 mt-2">Create your account</p>
        </div>

        <SignupForm />

        <p className="text-center mt-6 text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-600 hover:text-indigo-500 font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

