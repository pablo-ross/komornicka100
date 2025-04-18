import Link from 'next/link';
import useProjectName from '../hooks/useProjectName';
import PageTitle from '../components/PageTitle';

export default function ThankYou() {
  const projectName = useProjectName();

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Registration Complete" />
      
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-6 text-green-500">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        
        <h1 className="text-2xl font-bold mb-4">Thank You!</h1>
        
        <p className="mb-6">
          Your registration for {projectName} is now complete!
        </p>
        
        <div className="bg-gray-50 p-4 rounded-lg mb-6">
          <h2 className="text-lg font-semibold mb-2">What happens next?</h2>
          <ul className="text-left list-disc pl-5 space-y-2">
            <li>Our system will check your Strava account for bike activities every 2 hours between 6:00 and 22:00.</li>
            <li>Activities that match our route criteria will be automatically approved.</li>
            <li>You'll receive an email notification when your activity is approved.</li>
            <li>Your approved activities will count towards your position on the leaderboard.</li>
          </ul>
        </div>
        
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Route Requirements</h2>
          <p>Remember, to qualify, your activities must:</p>
          <ul className="text-left list-disc pl-5 space-y-1">
            <li>Be at least 100 kilometers in length</li>
            <li>Match one of our predefined routes</li>
            <li>Be recorded on Strava as a bike ride</li>
          </ul>
        </div>
        
        <Link href="/">
          <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
            View Leaderboard
          </span>
        </Link>
      </div>
    </div>
  );
}