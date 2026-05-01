'use client';

import Image from "next/image";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";

interface AETHER-SCORELogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
  className?: string;
  useImage?: boolean;
  imagePath?: string;
}

export function AETHER-SCORELogo({ 
  size = 'md', 
  showText = true, 
  className = '',
  useImage = true, // Default to using image logo
  imagePath = '/AETHER-SCORE-logo.svg' // Try SVG first, fallback to PNG
}: AETHER-SCORELogoProps) {
  const [imageError, setImageError] = useState(false);
  const [currentImagePath, setCurrentImagePath] = useState(imagePath);
  
  const sizeClasses = {
    sm: { icon: 'w-8 h-8', text: 'text-sm' },
    md: { icon: 'w-10 h-10', text: 'text-base' },
    lg: { icon: 'w-16 h-16', text: 'text-xl' },
  };

  const currentSize = sizeClasses[size];

  // Handle image error with proper state management (no DOM manipulation)
  const handleImageError = () => {
    if (currentImagePath.endsWith('.svg')) {
      // Try PNG version
      setCurrentImagePath('/AETHER-SCORE-logo.png');
    } else {
      // Fallback to built-in SVG
      setImageError(true);
    }
  };

  // Reset error state when imagePath changes
  useEffect(() => {
    setImageError(false);
    setCurrentImagePath(imagePath);
  }, [imagePath]);

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* Logo - Image or SVG */}
      {useImage && !imageError ? (
        <motion.div
          className={`${currentSize.icon} relative flex-shrink-0`}
          whileHover={{ scale: 1.05 }}
          transition={{ duration: 0.2 }}
        >
          <Image
            src={currentImagePath}
            alt="AETHER-SCORE Logo"
            width={size === 'sm' ? 32 : size === 'md' ? 40 : 64}
            height={size === 'sm' ? 32 : size === 'md' ? 40 : 64}
            className="object-contain"
            priority
            onError={handleImageError}
          />
        </motion.div>
      ) : (
        <motion.div
          className={`${currentSize.icon} rounded-xl relative flex items-center justify-center flex-shrink-0`}
          style={{
            background: 'linear-gradient(135deg, hsl(190, 100%, 50%) 0%, hsl(262, 83%, 58%) 100%)',
            boxShadow: '0 0 20px hsl(190, 100%, 50% / 0.4), 0 0 40px hsl(262, 83%, 58% / 0.3)',
          }}
          whileHover={{ scale: 1.05 }}
          transition={{ duration: 0.2 }}
        >
          {/* Glowing outline effect */}
          <div 
            className="absolute inset-0 rounded-xl"
            style={{
              background: 'linear-gradient(135deg, hsl(190, 100%, 50%) 0%, hsl(262, 83%, 58%) 100%)',
              filter: 'blur(4px)',
              opacity: 0.6,
              zIndex: -1,
            }}
          />
          
          {/* N Letter with gradient */}
          <span 
            className="text-xl font-bold font-mono relative z-10"
            style={{
              background: 'linear-gradient(135deg, hsl(195, 100%, 60%) 0%, hsl(270, 80%, 50%) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              filter: 'drop-shadow(0 0 8px hsl(190, 100%, 50% / 0.5))',
            }}
          >
            N
          </span>
        </motion.div>
      )}

      {/* Text */}
      {showText && (
        <motion.div
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
          className="flex flex-col"
        >
          <h1 className={`${currentSize.text} font-bold text-white whitespace-nowrap`}>
            AETHER-SCORE
          </h1>
          {size !== 'sm' && (
            <p className="text-xs text-muted-foreground whitespace-nowrap">
              Credit Passport
            </p>
          )}
        </motion.div>
      )}
    </div>
  );
}


