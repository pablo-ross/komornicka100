import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import useProjectName from '../../../hooks/useProjectName';
import StravaConnectButton from '../../../components/StravaConnectButton';
import Meta from '../../../components/Meta';

export default function StravaAuth() {
  const projectName = useProjectName();
  const router = useRouter();
  const { userId, token, code, frontend_redirect, error, error_description } = router.query;
  
  const [isConnecting, setIsConnecting] = useState(true);
  const [isSuccess, setIsSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [stravaAuthUrl, setStravaAuthUrl] = useState('');
  const [debugInfo, setDebugInfo] = useState({});

  useEffect(() => {
    // Only run once router is ready and we have the parameters
    if (!router.isReady) return;

    console.log("Router query params:", router.query);
    
    // Check if we're missing essential parameters
    if (!userId || !token) {
      setErrorMessage("Missing user ID or token");
      setIsConnecting(false);
      return;
    }

    // Check if there's an error from Strava
    if (error) {
      setErrorMessage(`Strava Error: ${error_description || error}`);
      setIsConnecting(false);
      return;
    }

    const handleStravaAuth = async () => {
      try {
        // Check if this is a redirect from Strava
        if (frontend_redirect === 'true' && code) {
          console.log("Processing auth callback with code:", code);
          
          // Process the authorization code
          const response = await fetch(`/api/strava/auth/${userId}/${token}?code=${code}`);
          
          console.log("API response status:", response.status);
          
          // Check for non-JSON responses (like HTML error pages)
          const contentType = response.headers.get("content-type");
          if (!contentType || !contentType.includes("application/json")) {
            throw new Error(`Server returned non-JSON response: ${contentType}`);
          }
          
          const data = await response.json();
          console.log("API response data:", data);
          
          if (!response.ok) {
            throw new Error(data.detail || 'Strava connection failed');
          }
          
          // Redirect to thank you page
          setIsSuccess(true);
          if (data.redirect_url) {
            // Give time to show success message before redirecting
            setTimeout(() => {
              window.location.href = data.redirect_url;
            }, 1500);
          } else {
            setTimeout(() => {
              router.push('/thank-you');
            }, 1500);
          }
          return;
        }

        // If not a redirect from Strava, get the auth URL
        console.log("Getting Strava auth URL for user:", userId);
        const url = `/api/strava/auth/${userId}/${token}`;
        
        const response = await fetch(url);
        console.log("Auth URL response status:", response.status);
        
        const data = await response.json();
        console.log("Auth URL response data:", data);
        
        if (!response.ok) {
          throw new Error(data.detail || 'Failed to get Strava authorization URL');
        }
        
        // If we have an auth URL, store it
        if (data.auth_url) {
          setStravaAuthUrl(data.auth_url);
          setIsConnecting(false);
          return;
        }
        
        // Unexpected response
        throw new Error('Unexpected response from server');
      } catch (error) {
        console.error('Error connecting to Strava:', error);
        setErrorMessage(error instanceof Error ? error.message : 'Something went wrong');
        
        // Collect debug info
        setDebugInfo({
          userId,
          token,
          code: code ? `${code.slice(0, 5)}...` : null,
          frontendRedirect: frontend_redirect,
          error: error instanceof Error ? error.message : String(error),
          time: new Date().toISOString()
        });
      } finally {
        setIsConnecting(false);
      }
    };

    handleStravaAuth();
  }, [router.isReady, userId, token, code, frontend_redirect, router, error, error_description]);

  // Redirect based on state
  if (frontend_redirect === 'true' && isConnecting) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-lg">
        <Meta title="Connecting to Strava" />
        
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
      <Meta title="Connect to Strava" />
      
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
        ) : errorMessage ? (
          <div>
            <div className="mb-4 text-red-500">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-4">Connection Failed</h2>
            <p className="text-red-500 mb-6">{errorMessage}</p>
            <p className="mb-4">
              There was an issue connecting your Strava account. Please try again.
            </p>
            
            {/* Debug information (hidden in production) */}
            {process.env.NODE_ENV === 'development' && (
              <div className="mt-4 p-4 bg-gray-100 text-left text-xs overflow-auto max-h-40 rounded">
                <p className="font-bold mb-2">Debug Info:</p>
                <pre>{JSON.stringify(debugInfo, null, 2)}</pre>
              </div>
            )}
            
            <div className="flex flex-col sm:flex-row justify-center mt-4 space-y-2 sm:space-y-0 sm:space-x-2">
              <Link href="/">
                <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
                  Back to Home
                </span>
              </Link>
              
              {stravaAuthUrl && (
                <button 
                  onClick={() => window.location.href = stravaAuthUrl}
                  className="inline-block bg-strava-orange hover:bg-[#E34402] text-white font-bold py-2 px-6 rounded"
                >
                  Try Again
                </button>
              )}
            </div>
          </div>
        ) : stravaAuthUrl ? (
          <div>
            <p className="mb-6">Please connect your Strava account to verify your activities.</p>
            <StravaConnectButton authUrl={stravaAuthUrl} />
          </div>
        ) : (
          <div>
            <p className="mb-4">Loading connection details...</p>
            <div className="loading mx-auto w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        )}
      </div>
    </div>
  );
}