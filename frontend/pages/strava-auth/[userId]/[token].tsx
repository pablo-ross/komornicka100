import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import useProjectName from '../../../hooks/useProjectName';
import PageTitle from '../../../components/PageTitle';

export default function StravaAuth() {
  const projectName = useProjectName();
  const router = useRouter();
  const { userId, token, code, frontend_redirect } = router.query;
  
  const [isConnecting, setIsConnecting] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [stravaAuthUrl, setStravaAuthUrl] = useState('');

  useEffect(() => {
    if (!userId || !token) {
      return;
    }

    const handleStravaAuth = async () => {
      try {
        // Check if this is a redirect from Strava with frontend_redirect=true
        if (frontend_redirect === 'true' && code) {
          // Process the authorization code
          const response = await fetch(`/api/strava/auth/${userId}/${token}?code=${code}`);
          const data = await response.json();
          
          if (!response.ok) {
            throw new Error(data.detail || 'Strava connection failed');
          }
          
          // Redirect to thank you page
          if (data.redirect_url) {
            window.location.href = data.redirect_url;
          } else {
            router.push('/thank-you');
          }
          return;
        }

        // Otherwise, handle normal flow (either get auth URL or process code)
        const url = code 
          ? `/api/strava/auth/${userId}/${token}?code=${code}`
          : `/api/strava/auth/${userId}/${token}`;
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.detail || 'Strava connection failed');
        }
        
        // If we have an auth URL, we need to redirect to Strava
        if (data.auth_url) {
          setStravaAuthUrl(data.auth_url);
          return;
        }
        
        // If we have a redirect URL, this was a successful callback
        if (data.redirect_url) {
          setIsSuccess(true);
          
          // Redirect to thank you page after a short delay
          setTimeout(() => {
            router.push(data.redirect_url);
          }, 3000);
        }
      } catch (error) {
        console.error('Error connecting to Strava:', error);
        setError(error instanceof Error ? error.message : 'Something went wrong');
        setIsSuccess(false);
      } finally {
        setIsConnecting(false);
      }
    };

    handleStravaAuth();
  }, [userId, token, code, frontend_redirect, router]);

  // If we have an auth URL, redirect to Strava
  useEffect(() => {
    if (stravaAuthUrl) {
      window.location.href = stravaAuthUrl;
    }
  }, [stravaAuthUrl]);

  // Render UI based on state
  if (frontend_redirect === 'true') {
    return (
      <div className="container mx-auto px-4 py-8 max-w-lg">
        <PageTitle title="Connecting to Strava" />
        
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <h1 className="text-2xl font-bold mb-6">Connecting to Strava</h1>
          <p>Please wait while we complete your Strava connection...</p>
          <div className="loading mt-4 mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Connect to Strava" />
      
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-2xl font-bold mb-6">Connect Your Strava Account</h1>
        
        {isConnecting ? (
          <div>
            <p>Preparing Strava connection...</p>
            <div className="loading mt-4 mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : isSuccess ? (
          <div>
            <div className="mb-4 text-green-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Strava Connected!</h2>
            <p className="mb-6">Your Strava account has been successfully connected.</p>
            <p>Redirecting you to the confirmation page...</p>
          </div>
        ) : (
          <div>
            <div className="mb-4 text-red-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Connection Failed</h2>
            <p className="text-red-500 mb-6">{error}</p>
            <p className="mb-4">
              There was an issue connecting your Strava account. Please try again.
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