"use client";
import { useEffect, useRef } from 'react';

export default function LatestVideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // Simple function to update the video source
  const updateVideo = () => {
    if (!videoRef.current) return;
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const videoUrl = `http://localhost:8002/latest?t=${timestamp}`;
    
    // Store the current source to revoke it later
    const previousSrc = videoRef.current.src;
    
    // Set the new source
    videoRef.current.src = videoUrl;
    
    // Revoke the old blob URL to free memory
    if (previousSrc) {
      URL.revokeObjectURL(previousSrc);
    }
    
    // Try to play the video
    videoRef.current.play().catch(e => {
      console.error('Error playing video:', e);
    });
  };
  
  // Initial load and set up polling
  useEffect(() => {
    // Initial update
    updateVideo();
    
    // Set up polling every 5 seconds
    const intervalId = setInterval(updateVideo, 5000);
    
    // Clean up on unmount
    return () => {
      clearInterval(intervalId);
      // Clean up the video source
      if (videoRef.current?.src) {
        URL.revokeObjectURL(videoRef.current.src);
      }
    };
  }, []);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      margin: 0,
      padding: 0,
      overflow: 'hidden',
      backgroundColor: 'black',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <video 
        ref={videoRef}
        width="1280"
        height="720"
        controls 
        autoPlay 
        muted 
        playsInline
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          objectFit: 'contain'
        }}
        onError={(e) => {
          console.error('Video error:', e);
          // Try to reload the video on error
          setTimeout(updateVideo, 1000);
        }}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
}
