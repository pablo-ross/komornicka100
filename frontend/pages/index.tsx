import { useEffect, useState } from 'react';
import Link from 'next/link';
import useProjectName from '../hooks/useProjectName';
import PageTitle from '../components/PageTitle';

type LeaderboardEntry = {
  first_name: string;
  last_name: string;
  activity_count: number;
};

export default function Home() {
  const projectName = useProjectName();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const response = await fetch('/api/activities/leaderboard');
        
        if (!response.ok) {
          throw new Error('Failed to fetch leaderboard');
        }
        
        const data = await response.json();
        setLeaderboard(data);
      } catch (err) {
        setError('Error loading leaderboard. Please try again later.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLeaderboard();
  }, []);

  return (
    <div className="container mx-auto px-4 py-8">
      <PageTitle title="Home" />
      
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">{projectName}</h1>
        
        <div className="mb-8 text-center">
          <p className="mb-4">
            Welcome to the {projectName}! Track your bike rides and compete with other riders.
          </p>
          <Link href="/register">
            <span className="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded">
              Register Now
            </span>
          </Link>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">Leaderboard</h2>
          
          {isLoading ? (
            <p className="text-center py-4">Loading leaderboard...</p>
          ) : error ? (
            <p className="text-red-500 text-center py-4">{error}</p>
          ) : leaderboard.length === 0 ? (
            <p className="text-center py-4">No participants yet. Be the first one to register!</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-4 py-2 text-left">Rank</th>
                    <th className="px-4 py-2 text-left">Name</th>
                    <th className="px-4 py-2 text-right">Activities</th>
                  </tr>
                </thead>
                <tbody>
                  {leaderboard.map((entry, index) => (
                    <tr key={index} className="border-b">
                      <td className="px-4 py-2">{index + 1}</td>
                      <td className="px-4 py-2">
                        {entry.first_name} {entry.last_name}
                      </td>
                      <td className="px-4 py-2 text-right">{entry.activity_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600">
            Powered by Komorniki MTB Team & Mornel | 
            <Link href="/terms" className="text-blue-500 ml-1">
              Terms & Regulations
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}