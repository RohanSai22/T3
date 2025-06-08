import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { CognitiveBlockData, ThoughtType } from '@/types'; // Assuming types.ts is in src

interface CognitiveBlockProps {
  data: CognitiveBlockData;
}

const getIconForType = (type: ThoughtType): string => {
  switch (type) {
    case "Hypothesis":
      return "💡"; // Lightbulb
    case "Action":
      return "⚙️"; // Gear (or 🔍 for Magnifying glass)
    case "Analysis":
      return "📊"; // Bar chart
    case "Strategy":
      return "📝"; // Memo
    case "Error":
      return "⚠️"; // Warning
    default:
      return "🧠"; // Brain for unknown
  }
};

export const CognitiveBlock: React.FC<CognitiveBlockProps> = ({ data }) => {
  const { type, title, details, timestamp } = data;
  const icon = getIconForType(type);

  return (
    <Card className="mb-3 cognitive-block-fade-in bg-neutral-700 border-neutral-600 text-neutral-100 shadow-md">
      <CardHeader className="pb-2 pt-3 px-4">
        <CardTitle className="text-sm font-medium flex items-center text-neutral-200"> {/* Slightly muted title */}
          <span className="mr-2 text-md">{icon}</span> {/* Adjusted icon size */}
          {title}
        </CardTitle>
      </CardHeader>
      {details && (
        <CardContent className="text-xs px-4 pb-2 text-neutral-300"> {/* Smaller details text */}
          {Array.isArray(details) ? (
            <ul className="list-disc pl-4 space-y-0.5"> {/* Adjusted list styling */}
              {details.map((item, index) => (
                <li key={index} className="break-words">{item}</li>
              ))}
            </ul>
          ) : (
            <p className="break-words">{details}</p>
          )}
        </CardContent>
      )}
      <CardFooter className="text-xs text-neutral-400 px-4 pb-2 pt-1"> {/* Slightly less muted footer */}
        {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
      </CardFooter>
    </Card>
  );
};
