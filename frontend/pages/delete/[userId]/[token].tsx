import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import useProjectName from '../../../hooks/useProjectName';
import PageTitle from '../../../components/PageTitle';

export default function DeleteAccount() {
  const projectName = useProjectName();
  const router = useRouter();
  const { userId, token } = router.query;
  
  const [isProcessing, setIsProcessing] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!userId || !token) {
      return;
    }

    const deleteAccount = async () => {
      try {
        const response = await fetch(`/api/users/delete/${userId}/${token}`);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || 'Account deletion failed');
        }
        
        setIsSuccess(true);
      } catch (error) {
        // Handle the error with proper TypeScript type checking
        setError(error instanceof Error ? error.message : 'Something went wrong');
        setIsSuccess(false);
      } finally {
        setIsProcessing(false);
      }
    };

    deleteAccount();
  }, [userId, token]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Account Deletion" />
      
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-2xl font-bold mb-6">Account Deletion</h1>
        
        {isProcessing ? (
          <div>
            <p>Processing your account deletion request...</p>
            <div className="loading mt-4 mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : isSuccess ? (
          <div>
            <div className="mb-4 text-green-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Account Successfully Deleted</h2>
            <p className="mb-6">
              Your account and all associated data have been deleted from {projectName}.
            </p>
            <p className="mb-6">
              We're sorry to see you go. If you change your mind, you're welcome to register again in the future.
            </p>
            <Link href="/">
              <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
                Back to Home
              </span>
            </Link>
          </div>
        ) : (
          <div>
            <div className="mb-4 text-red-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Deletion Failed</h2>
            <p className="text-red-500 mb-6">{error}</p>
            <p className="mb-4">
              This deletion link may have expired or already been used.
            </p>
            <Link href="/">
              <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
                Back to Home
              </span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}