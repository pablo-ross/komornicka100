// frontend/components/DebugPanel.tsx
import React, { useState } from 'react';

interface DebugPanelProps {
  data: any;
  title?: string;
}

const DebugPanel: React.FC<DebugPanelProps> = ({ data, title = 'Debug Information' }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="mt-4 p-2 border border-gray-300 rounded bg-gray-50">
      <div 
        className="flex justify-between items-center cursor-pointer" 
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="text-sm font-semibold">{title}</h3>
        <span>{isExpanded ? '▼' : '▶'}</span>
      </div>
      
      {isExpanded && (
        <div className="mt-2 p-2 bg-white border border-gray-200 rounded overflow-auto max-h-60">
          <pre className="text-xs">{JSON.stringify(data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default DebugPanel;