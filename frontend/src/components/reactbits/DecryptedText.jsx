import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

/**
 * DecryptedText from React Bits
 * Decrypts / scrambles text into the final string character-by-character.
 */
export default function DecryptedText({
  text = '',
  speed = 40,
  maxIterations = 10,
  sequential = true,
  revealDirection = 'start',
  useOriginalCharsOnly = false,
  characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz!@#$%^&*()_+~`|}{[]:;?><,./-=',
  className = '',
  parentClassName = '',
  encryptedClassName = '',
  animateOn = 'view',
  ...props
}) {
  const [displayText, setDisplayText] = useState(text);
  const [isHovering, setIsHovering] = useState(false);
  const [isScrambling, setIsScrambling] = useState(false);
  const [revealedIndices, setRevealedIndices] = useState(new Set());
  const [hasAnimated, setHasAnimated] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    let interval;
    let currentIteration = 0;

    const getNextChar = (char) => {
      if (char === ' ') return ' ';
      if (useOriginalCharsOnly) {
        const availableChars = text.replace(/\s/g, '');
        return availableChars[Math.floor(Math.random() * availableChars.length)];
      }
      return characters[Math.floor(Math.random() * characters.length)];
    };

    const startScrambling = () => {
      setIsScrambling(true);
      interval = setInterval(() => {
        setDisplayText((prevText) => {
          return text
            .split('')
            .map((char, index) => {
              if (char === ' ') return ' ';
              if (revealedIndices.has(index)) return char;

              if (sequential) {
                if (revealDirection === 'start' && index <= (currentIteration / maxIterations) * text.length) {
                  setRevealedIndices((prev) => new Set(prev).add(index));
                  return char;
                }
                if (revealDirection === 'end' && index >= text.length - (currentIteration / maxIterations) * text.length) {
                  setRevealedIndices((prev) => new Set(prev).add(index));
                  return char;
                }
              }

              if (currentIteration >= maxIterations) {
                setRevealedIndices((prev) => new Set(prev).add(index));
                return char;
              }

              return getNextChar(char);
            })
            .join('');
        });

        currentIteration++;
        if (currentIteration > maxIterations * 1.5) {
          clearInterval(interval);
          setIsScrambling(false);
          setDisplayText(text);
        }
      }, speed);
    };

    if (animateOn === 'view' && !hasAnimated) {
      startScrambling();
      setHasAnimated(true);
    } else if (animateOn === 'hover' && isHovering && !isScrambling) {
      setRevealedIndices(new Set());
      currentIteration = 0;
      startScrambling();
    }

    return () => clearInterval(interval);
  }, [text, speed, maxIterations, sequential, revealDirection, isHovering, animateOn, hasAnimated]);

  return (
    <motion.span
      ref={containerRef}
      className={`inline-block ${parentClassName}`}
      onMouseEnter={() => setIsHovering(true)}
      onMouseLeave={() => setIsHovering(false)}
      {...props}
    >
      <span className={className}>
        {displayText.split('').map((char, index) => {
          const isRevealed = revealedIndices.has(index) || char === ' ' || !isScrambling;
          return (
            <span
              key={index}
              className={isRevealed ? '' : encryptedClassName || 'text-[#B23A2E] opacity-75'}
            >
              {char}
            </span>
          );
        })}
      </span>
    </motion.span>
  );
}
