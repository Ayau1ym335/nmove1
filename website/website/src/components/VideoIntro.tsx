import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { X } from 'lucide-react';

interface VideoIntroProps {
    onComplete: () => void;
    videoSrc: string;
}

export const VideoIntro: React.FC<VideoIntroProps> = ({ onComplete, videoSrc }) => {
    const [isVisible, setIsVisible] = useState(true);
    const videoRef = useRef<HTMLVideoElement>(null);

    const handleSkip = () => {
        setIsVisible(false);
        setTimeout(onComplete, 500); // Wait for fade out animation
    };

    useEffect(() => {
        // Prevent scrolling while intro is visible
        document.body.style.overflow = 'hidden';

        return () => {
            document.body.style.overflow = 'unset';
        };
    }, []);

    return (
        <div
            className={`fixed inset-0 z-[9999] flex items-center justify-center bg-black transition-opacity duration-500 ${isVisible ? 'opacity-100' : 'opacity-0 pointer-events-none'
                }`}
        >
            <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                onEnded={handleSkip}
                className="w-full h-full object-cover"
            >
                <source src={videoSrc} type="video/mp4" />
                Your browser does not support the video tag.
            </video>

            <div className="absolute bottom-10 right-10 z-10">
                <Button
                    onClick={handleSkip}
                    variant="secondary"
                    className="bg-white/10 hover:bg-white/20 text-white border-white/20 backdrop-blur-md px-6 py-2 rounded-full transition-all hover:scale-105"
                >
                    Skip Intro
                </Button>
            </div>

            {/* Optional: Close icon as well */}
            <button
                onClick={handleSkip}
                className="absolute top-10 right-10 text-white/50 hover:text-white transition-colors"
            >
                <X size={32} />
            </button>
        </div>
    );
};
