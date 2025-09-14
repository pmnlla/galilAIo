
"use client";

import useSWR from "swr";

const fetcher = (url: string) => fetch(url).then((res) => res.blob());

export default function VideoPlayerPage() {
  const videoEndpoint = "http://localhost:8002/latest";

  const { data, error, isLoading, mutate } = useSWR(videoEndpoint, fetcher, {
    refreshInterval: 3000, // Poll every 3 seconds
    revalidateOnFocus: false,
  });

  if (error) {
    return <div>Error loading video</div>;
  }

  if (isLoading) {
    return <div>Loading video...</div>;
  }

  const videoUrl = data ? URL.createObjectURL(data) : null;

  return (
    <div className="flex flex-col items-center justify-center w-full h-full py-2">
      {videoUrl ? (
        <div className="w-full">
          <video
            key={videoUrl} // Force re-render if URL changes
            src={videoUrl}
            autoPlay
            muted
            className="w-full rounded-lg"
          />
        </div>
      ) : (
        <div>No video available</div>
      )}
    </div>
  );
}
