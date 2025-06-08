import React, { useState, useEffect, useRef } from 'react';

interface CustomTextEffectProps {
  text: string;
  baseClass?: string;
  charClass?: string;
  animationDelay?: number; // milliseconds
  animationDuration?: string; // e.g., '1s'
  finalClass?: string; // class to apply after animation
}

const CustomTextEffect: React.FC<CustomTextEffectProps> = ({
  text,
  baseClass = "",
  charClass = "",
  animationDelay = 50, // Default delay between characters
  animationDuration = '0.5s', // Default animation duration for each char
  finalClass = "", // Default no final class override
}) => {
  const [animatedChars, setAnimatedChars] = useState<React.ReactNode[]>([]);
  const [isAnimationComplete, setIsAnimationComplete] = useState(false);
  const chars = text.split('');
  const timeoutIds = useRef<NodeJS.Timeout[]>([]);

  useEffect(() => {
    // Clear any existing timeouts when text changes or component unmounts
    timeoutIds.current.forEach(clearTimeout);
    timeoutIds.current = [];
    setAnimatedChars([]);
    setIsAnimationComplete(false);

    const newAnimatedChars = chars.map((char, index) => {
      const timeoutId = setTimeout(().tsx
        setAnimatedChars(prev => {
          const newChars = [...prev];
          newChars[index] = (
            <span
              key={`${char}-${index}-animated`}
              className={`${charClass} inline-block opacity-0 animate-fadeInUp`}
              style={{
                animationDuration: animationDuration,
                animationFillMode: 'forwards',
              }}
            >
              {char === ' ' ? '\u00A0' : char}
            </span>
          );
          return newChars;
        });

        // Check if this is the last character to set animation complete
        if (index === chars.length - 1) {
          // Set a timeout for when the last character's animation should be done
          const lastCharAnimDurationMs = parseFloat(animationDuration) * (animationDuration.endsWith('ms') ? 1 : 1000);
          const finalTimeoutId = setTimeout(() => {
            setIsAnimationComplete(true);
          }, lastCharAnimDurationMs);
          timeoutIds.current.push(finalTimeoutId);
        }
      }, index * animationDelay);
      timeoutIds.current.push(timeoutId);

      // Initial state (can be empty or placeholder before animation if preferred)
      return (
        <span key={`${char}-${index}-initial`} className="opacity-0">
          {char === ' ' ? '\u00A0' : char}
        </span>
      );
    });

    setAnimatedChars(newAnimatedChars); // Set initial placeholders

    // Cleanup function to clear timeouts
    return () => {
      timeoutIds.current.forEach(clearTimeout);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, charClass, animationDelay, animationDuration]); // Rerun when these change

  if (isAnimationComplete && finalClass) {
    return <div className={`${baseClass} ${finalClass}`}>{text}</div>;
  }

  return (
    <div className={baseClass}>
      {animatedChars.map((node, index) => (
        <React.Fragment key={index}>{node}</React.Fragment>
      ))}
    </div>
  );
};

export default CustomTextEffect;
