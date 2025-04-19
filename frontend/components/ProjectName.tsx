import React from 'react';
import ClientOnly from './ClientOnly';
import useProjectName from '../hooks/useProjectName';

export function ProjectName(): JSX.Element {
  const projectName = useProjectName();
  
  return (
    <ClientOnly>
      <span>{projectName}</span>
    </ClientOnly>
  );
}