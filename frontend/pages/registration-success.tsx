import Link from 'next/link';
import useProjectName from '../hooks/useProjectName';
import PageTitle from '../components/PageTitle';

export default function RegistrationSuccess() {
  const projectName = useProjectName();

  return (
    <div className="container mx-auto px-4 py-8 max-w-lg">
      <PageTitle title="Registration Successful" />
      
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="mb-6 text-green-500">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        
        <h1 className="text-2xl font-bold mb-4">Registration Successful!</h1>
        
        <p className="mb-6">
          Thank you for registering for the {projectName}!
        </p>
        
        <div className="bg-blue-50 p-4 rounded-lg mb-6 text-left">
          <h2 className="text-lg font-semibold mb-2">Next Steps:</h2>
          <ol className="list-decimal pl-5 space-y-2">
            <li>
              <strong>Check your email</strong> - We've sent a verification link to your email address.
            </li>
            <li>
              <strong>Verify your email</strong> - Click the link in the email to verify your account.
            </li>
            <li>
              <strong>Connect Strava</strong> - After verification, you'll be asked to connect your Strava account.
            </li>
          </ol>
        </div>
        
        <div className="mb-6 text-left">
          <h2 className="text-lg font-semibold mb-2">Important:</h2>
          <ul className="list-disc pl-5 space-y-1">
            <li>Please check your spam/junk folder if you don't see the email in your inbox.</li>
            <li>The verification link will expire in 48 hours.</li>
            <li>You must complete all steps to fully register for the contest.</li>
          </ul>
        </div>
        
        <Link href="/">
          <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
            Back to Home
          </span>
        </Link>
      </div>
    </div>
  );
}