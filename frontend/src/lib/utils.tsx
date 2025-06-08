import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import React from "react";
import { Source, E2BArtifact } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatMessageWithInteractiveElements(
  message: string,
  sources: Source[],
  artifacts: E2BArtifact[]
): React.ReactNode[] {
  const parts: (string | React.ReactNode)[] = [];
  let lastIndex = 0;

  // Regex for all markers: [1], [IMAGE: name.png], [HTML_OUTPUT: name.html]
  // It captures the type (number, IMAGE, HTML_OUTPUT) and the value (number or filename)
  const markerRegex =
    /\[(?:(\d+)|(IMAGE:\s*([^\]]+))|(HTML_OUTPUT:\s*([^\]]+)))\]/g;
  let match;

  while ((match = markerRegex.exec(message)) !== null) {
    const fullMatchString = match[0]; // e.g., "[1]", "[IMAGE: plot.png]"
    const markerIndex = match.index;

    // Add text part before the current marker
    if (markerIndex > lastIndex) {
      parts.push(message.substring(lastIndex, markerIndex));
    }

    let replacementNode: React.ReactNode = fullMatchString; // Default to original marker text

    if (match[1]) {
      // Numeric citation like [1]
      const markerNumber = parseInt(match[1], 10);
      const numericMarker = `[${markerNumber}]`;
      const source = sources.find((s) => s.citation_marker === numericMarker);
      if (source) {
        replacementNode = (
          <a
            key={`${numericMarker}-${markerIndex}`}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 underline"
            title={source.title}
          >
            {numericMarker}
          </a>
        );
      }
    } else if (match[3]) {
      // Image marker like [IMAGE: filename.png]
      const imageName = match[3].trim();
      const artifact = artifacts.find(
        (a) => a.name === imageName && a.type === "image" && a.data_uri
      );
      if (artifact) {
        replacementNode = (
          <img
            key={`${imageName}-${markerIndex}`}
            src={artifact.data_uri}
            alt={artifact.name}
            className="max-w-sm h-auto rounded-md my-2 border border-neutral-600"
          />
        );
      }
    } else if (match[5]) {
      // HTML output marker like [HTML_OUTPUT: filename.html]
      const htmlName = match[5].trim();
      const artifact = artifacts.find(
        (a) => a.name === htmlName && a.type === "html_content" && a.content
      );
      if (artifact && artifact.content) {
        // Option: Render in a sandboxed iframe
        replacementNode = (
          <div key={`${htmlName}-${markerIndex}`} className="my-2">
            <p className="text-sm text-neutral-400 mb-1">
              Interactive Output: {htmlName}
            </p>
            <iframe
              srcDoc={artifact.content}
              sandbox="allow-scripts"
              className="w-full h-64 border border-neutral-600 rounded-md"
              title={htmlName}
            />
          </div>
        );
        // Option: Link to data URI (simpler, opens in new tab)
        // const dataUri = `data:text/html;charset=utf-8,${encodeURIComponent(artifact.content)}`;
        // replacementNode = (
        //   <a key={`${htmlName}-${markerIndex}`} href={dataUri} target="_blank" rel="noopener noreferrer" className="text-green-400 hover:text-green-300 underline">
        //     View Interactive Output: {htmlName}
        //   </a>
        // );
      }
    }

    parts.push(replacementNode);
    lastIndex = markerRegex.lastIndex;
  }

  // Add remaining text part
  if (lastIndex < message.length) {
    parts.push(message.substring(lastIndex));
  }

  // Filter out empty strings that might result from consecutive markers
  return parts.filter((part) => part !== "");
}
