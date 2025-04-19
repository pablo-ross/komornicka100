import React from 'react';
import { addPlatformToUrl, detectPlatform, isMobile } from '../utils/platformDetection';

interface StravaConnectButtonProps {
  authUrl: string;
  className?: string;
}

const StravaConnectButton: React.FC<StravaConnectButtonProps> = ({ authUrl, className = '' }) => {
  const platform = detectPlatform();
  
  const handleStravaConnect = () => {
    if (!authUrl) return;
    
    let url = authUrl;
    
    // Add platform parameter to URL
    url = addPlatformToUrl(url);
    
    // Open the authorization URL
    window.location.href = url;
  };
  
  return (
    <button
      onClick={handleStravaConnect}
      className={`flex items-center justify-center bg-strava-orange hover:bg-[#E34402] text-white font-bold py-3 px-6 rounded ${className}`}
      aria-label="Connect with Strava"
      data-platform={platform}
    >
      <svg viewBox="0 0 24 24" className="w-5 h-5 mr-2" fill="currentColor">
        <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
      </svg>
      Connect with Strava
    </button>
  );
};

export default StravaConnectButton;