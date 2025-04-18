import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import useProjectName from '../../../hooks/useProjectName';
import PageTitle from '../../../components/PageTitle';

export default function EmailVerify() {
  const projectName = useProjectName();
  const router = useRouter();
  const { userId, token } = router.query;
  
  const [isVerifying, setIsVerifying] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [stravaAuthUrl, setStravaAuthUrl] = useState('');

  useEffect(() => {
    if (!userId || !token) {
      return;
    }

    const verifyEmail = async () => {
      try {
        const response = await fetch(`/api/users/verify/${userId}/${token}`);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || 'Email verification failed');
        }
        
        setIsSuccess(true);
        
        // If verification is successful, the API returns a Strava auth URL
        if (data.strava_auth_url) {
          setStravaAuthUrl(data.strava_auth_url);
        }
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Something went wrong');
        setIsSuccess(false);
      } finally {
        setIsVerifying(false);
      }
    };

    verifyEmail();
  }, [userId, token]);

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Email Verification" />
      
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-2xl font-bold mb-6">Email Verification</h1>
        
        {isVerifying ? (
          <div>
            <p>Verifying your email address...</p>
            <div className="loading mt-4 mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : isSuccess ? (
          <div>
            <div className="mb-4 text-green-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Email Verified!</h2>
            <p className="mb-6">Your email has been successfully verified.</p>
            
            {stravaAuthUrl ? (
              <div>
                <p className="mb-4">The next step is to connect your Strava account.</p>
                <a 
                  href={stravaAuthUrl}
                  className="inline-block bg-[#FC4C02] hover:bg-[#E34402] text-white font-bold py-2 px-6 rounded"
                >
                  Connect with Strava
                </a>
              </div>
            ) : (
              <Link href="/">
                <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
                  Back to Home
                </span>
              </Link>
            )}
          </div>
        ) : (
          <div>
            <div className="mb-4 text-red-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Verification Failed</h2>
            <p className="text-red-500 mb-6">{error}</p>
            <p className="mb-4">
              This verification link may have expired or already been used.
            </p>
            <Link href="/register">
              <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
                Back to Registration
              </span>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}