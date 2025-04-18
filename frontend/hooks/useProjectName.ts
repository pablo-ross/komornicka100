import { useEffect, useState } from 'react';

export default function useProjectName(): string {
  const [projectName, setProjectName] = useState('Komornicka 100');

  useEffect(() => {
    // Try to get the project name from the environment variable
    const envProjectName = process.env.NEXT_PUBLIC_PROJECT_NAME;
    if (envProjectName) {
      setProjectName(envProjectName);
    }
  }, []);

  return projectName;
}