"use client";
import { useEffect, useRef, useState } from 'react';

export default function LatestVideo() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Simple function to update the video source
  const updateVideo = async () => {
    if (!videoRef.current || isLoading) return;
    
    const video = videoRef.current;
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const videoUrl = `http://localhost:8002/latest?t=${timestamp}`;
    
    // Check if the source has actually changed (ignoring timestamp)
    const currentSrcWithoutTimestamp = video.src?.split('?t=')[0];
    const newSrcWithoutTimestamp = videoUrl.split('?t=')[0];
    
    if (currentSrcWithoutTimestamp === newSrcWithoutTimestamp && video.src) {
      // Source hasn't changed, no need to reload
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Pause current video and reset
      video.pause();
      video.currentTime = 0;
      
      // Store the current source to revoke it later
      const previousSrc = video.src;
      
      // Set the new source
      video.src = videoUrl;
      
      // Revoke the old blob URL to free memory (only if it's a blob URL)
      if (previousSrc && previousSrc.startsWith('blob:')) {
        URL.revokeObjectURL(previousSrc);
      }
      
      // Wait for the video to be ready before playing
      await new Promise<void>((resolve, reject) => {
        const onCanPlay = () => {
          video.removeEventListener('canplay', onCanPlay);
          video.removeEventListener('error', onError);
          resolve();
        };
        
        const onError = (e: Event) => {
          video.removeEventListener('canplay', onCanPlay);
          video.removeEventListener('error', onError);
          reject(new Error('Video failed to load'));
        };
        
        video.addEventListener('canplay', onCanPlay);
        video.addEventListener('error', onError);
        
        // Load the video
        video.load();
      });
      
      // Now try to play the video
      await video.play();
      
    } catch (error) {
      console.error('Error updating video:', error);
    } finally {
      setIsLoading(false);
    }
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
      // Clean up the video source (only if it's a blob URL)
      if (videoRef.current?.src && videoRef.current.src.startsWith('blob:')) {
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
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          color: 'white',
          fontSize: '14px',
          zIndex: 10
        }}>
          Loading...
        </div>
      )}
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
          setIsLoading(false);
          // Try to reload the video on error after a delay
          setTimeout(() => {
            if (!isLoading) {
              updateVideo();
            }
          }, 2000);
        }}
      >
        Your browser does not support the video tag.
      </video>
    </div>
  );
}
