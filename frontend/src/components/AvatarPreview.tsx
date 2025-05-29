import React from 'react';
import { Box, Paper, useMantineTheme } from '@mantine/core';
import { AvatarCustomization } from '../services/api';

interface AvatarPreviewProps {
    emoji: string;
    color: string;
    customization?: AvatarCustomization;
    size?: number;
}

const AvatarPreview: React.FC<AvatarPreviewProps> = ({ 
    emoji, 
    color, 
    customization,
    size = 200 
}) => {
    const theme = useMantineTheme();

    // Hat styles mapping
    const hatStyles: Record<string, string> = {
        cap: '🧢',
        beanie: '🎩',
        wizard: '🧙',
        crown: '👑',
        cowboy: '🤠',
        party: '🥳',
        santa: '🎅',
    };

    // Accessory styles mapping
    const accessoryStyles: Record<string, string> = {
        glasses: '👓',
        sunglasses: '🕶️',
        monocle: '🧐',
        eyepatch: '🏴‍☠️',
    };

    // Hair styles (as text overlay for now)
    const hairStyles: Record<string, string> = {
        short: '💇',
        long: '💁',
        spiky: '🦔',
        curly: '🦱',
        bald: '👨‍🦲',
    };

    // Outfit styles
    const outfitStyles: Record<string, string> = {
        casual: '👕',
        formal: '👔',
        superhero: '🦸',
        ninja: '🥷',
        doctor: '👨‍⚕️',
        chef: '👨‍🍳',
        astronaut: '👨‍🚀',
    };

    const backgroundStyle = customization?.background_color || color;

    return (
        <Paper
            shadow="sm"
            radius="50%"
            style={{
                width: size,
                height: size,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                backgroundColor: backgroundStyle,
                overflow: 'hidden',
            }}
        >
            {/* Background pattern */}
            {customization?.background === 'stars' && (
                <Box
                    style={{
                        position: 'absolute',
                        inset: 0,
                        background: `radial-gradient(circle, transparent 20%, ${backgroundStyle} 20.5%, ${backgroundStyle} 30%, transparent 30.5%, transparent), radial-gradient(circle, transparent 20%, ${backgroundStyle} 20.5%, ${backgroundStyle} 30%, transparent 30.5%, transparent) 25px 25px`,
                        backgroundSize: '50px 50px',
                        opacity: 0.3,
                    }}
                />
            )}
            
            {/* Main emoji/character */}
            <Box
                style={{
                    fontSize: size * 0.5,
                    lineHeight: 1,
                    position: 'relative',
                    zIndex: 1,
                }}
            >
                {emoji}
            </Box>

            {/* Hat overlay */}
            {customization?.hat && hatStyles[customization.hat] && (
                <Box
                    style={{
                        position: 'absolute',
                        top: 0,
                        fontSize: size * 0.3,
                        filter: customization.hat_color ? `hue-rotate(${getHueRotation(customization.hat_color)}deg)` : undefined,
                    }}
                >
                    {hatStyles[customization.hat]}
                </Box>
            )}

            {/* Accessory overlay */}
            {customization?.accessory && accessoryStyles[customization.accessory] && (
                <Box
                    style={{
                        position: 'absolute',
                        top: '35%',
                        fontSize: size * 0.25,
                        filter: customization.accessory_color ? `hue-rotate(${getHueRotation(customization.accessory_color)}deg)` : undefined,
                    }}
                >
                    {accessoryStyles[customization.accessory]}
                </Box>
            )}

            {/* Outfit overlay */}
            {customization?.outfit && outfitStyles[customization.outfit] && (
                <Box
                    style={{
                        position: 'absolute',
                        bottom: 0,
                        fontSize: size * 0.3,
                        filter: customization.outfit_color ? `hue-rotate(${getHueRotation(customization.outfit_color)}deg)` : undefined,
                    }}
                >
                    {outfitStyles[customization.outfit]}
                </Box>
            )}
        </Paper>
    );
};

// Helper function to calculate hue rotation from hex color
function getHueRotation(hexColor: string): number {
    // Simple hue rotation calculation
    const hex = hexColor.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const delta = max - min;
    
    let hue = 0;
    if (delta !== 0) {
        if (max === r) {
            hue = ((g - b) / delta) % 6;
        } else if (max === g) {
            hue = (b - r) / delta + 2;
        } else {
            hue = (r - g) / delta + 4;
        }
        hue = Math.round(hue * 60);
        if (hue < 0) hue += 360;
    }
    
    return hue;
}

export default AvatarPreview;