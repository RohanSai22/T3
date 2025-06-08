import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { CognitiveBlockData, ThoughtType } from '@/types';
import { Lightbulb, Zap, BarChart3, ListChecks, AlertTriangle, Brain } from 'lucide-react'; // Updated icons

interface CognitiveBlockProps {
  data: CognitiveBlockData;
}

const getIconForType = (type: ThoughtType): React.ReactNode => {
  const iconProps = { size: 16, className: "mr-2 flex-shrink-0" };
  switch (type) {
    case "Hypothesis":
      return <Lightbulb {...iconProps} color="#facc15" />; // Yellow
    case "Action":
      return <Zap {...iconProps} color="#38bdf8" />;       // Sky Blue
    case "Analysis":
      return <BarChart3 {...iconProps} color="#a78bfa" />; // Violet
    case "Strategy":
      return <ListChecks {...iconProps} color="#34d399" />; // Emerald Green
    case "Error":
      return <AlertTriangle {...iconProps} color="#f87171" />; // Red
    default:
      return <Brain {...iconProps} color="#9ca3af" />;      // Gray
  }
};

export const CognitiveBlock: React.FC<CognitiveBlockProps> = ({ data }) => {
  const { type, title, details, timestamp } = data;
  const icon = getIconForType(type);

  // Ensure details is always an array for consistent mapping
  const detailsArray = Array.isArray(details) ? details : (details ? [details] : []);

  return (
    <Card className="cognitive-block-fade-in bg-neutral-800/70 border-neutral-700/80 text-neutral-100 shadow-md mb-2 last:mb-0">
      <CardHeader className="pb-1.5 pt-2.5 px-3">
        <CardTitle className="text-xs font-semibold flex items-center text-neutral-200 truncate">
          {icon}
          <span className="truncate" title={title}>{title}</span>
        </CardTitle>
      </CardHeader>
      {detailsArray.length > 0 && (
        <CardContent className="text-xs px-3 pb-2 text-neutral-300">
          {detailsArray.length === 1 && typeof detailsArray[0] === 'string' && detailsArray[0].length < 150 ? (
            // Render as simple paragraph if single, short string
            <p className="break-words whitespace-pre-wrap">{detailsArray[0]}</p>
          ) : (
            // Render as list for multiple items or long single strings
            <ul className="list-disc pl-4 space-y-0.5">
              {detailsArray.map((item, index) => (
                <li key={index} className="break-words whitespace-pre-wrap">{typeof item === 'object' ? JSON.stringify(item) : item}</li>
              ))}
            </ul>
          )}
        </CardContent>
      )}
      <CardFooter className="text-[10px] text-neutral-500 px-3 pb-1.5 pt-0.5">
        {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
      </CardFooter>
    </Card>
  );
};
