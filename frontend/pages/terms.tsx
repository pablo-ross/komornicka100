import Link from 'next/link';
import useProjectName from '../hooks/useProjectName';
import PageTitle from '../components/PageTitle';

export default function Terms() {
  const projectName = useProjectName();

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <PageTitle title="Terms and Regulations" />
      
      <div className="bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold mb-6">
          Terms and Regulations - {projectName}
        </h1>
        
        <div className="prose max-w-none">
          <h2>1. General Provisions</h2>
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl.
          </p>
          
          <h2>2. Participation Requirements</h2>
          <p>
            Participation in the contest is open to all individuals who:
          </p>
          <ul>
            <li>Are at least 18 years of age</li>
            <li>Have a Strava account</li>
            <li>Agree to these terms and regulations</li>
            <li>Agree to the processing of personal data as described in section 6</li>
          </ul>
          
          <h2>3. Contest Rules</h2>
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl.
          </p>
          
          <h2>4. Verification Process</h2>
          <p>
            To qualify for the contest, participants must:
          </p>
          <ul>
            <li>Complete bike rides that match one of the predefined routes</li>
            <li>Record the activity using Strava</li>
            <li>Ensure the activity is at least 100 kilometers in length</li>
            <li>Allow the system to automatically verify the activity</li>
          </ul>
          <p>
            The system uses GPS data to compare participant routes with predefined routes. 
            Some deviation (up to 20 meters) is allowed to account for GPS inaccuracies.
          </p>
          
          <h2>5. Ranking and Prizes</h2>
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl.
          </p>
          
          <h2>6. Personal Data Processing</h2>
          <p>
            By participating in the contest, you agree to the processing of your personal data for the purpose of:
          </p>
          <ul>
            <li>Registering and managing your participation in the contest</li>
            <li>Verifying your activities</li>
            <li>Displaying your name on the leaderboard</li>
            <li>Communicating with you via email about your activities and contest updates</li>
          </ul>
          <p>
            Your personal data will be stored for the duration of the contest and will be deleted upon your request 
            or within 30 days after the conclusion of the contest.
          </p>
          
          <h2>7. Final Provisions</h2>
          <p>
            Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl. Nullam auctor, nisl eget ultricies tincidunt, 
            nunc nisl aliquam nisl, eget aliquam nisl nunc eget nisl.
          </p>
        </div>
        
        <div className="mt-8 text-center">
          <Link href="/register">
            <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
              Back to Registration
            </span>
          </Link>
        </div>
      </div>
    </div>
  );
}