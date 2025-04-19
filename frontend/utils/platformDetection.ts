/**
 * Utility for detecting device platform
 */

export type Platform = 'web' | 'android' | 'ios' | 'unknown';

/**
 * Detect the current device platform
 * 
 * @returns Platform identifier ('web', 'android', 'ios', or 'unknown')
 */
export function detectPlatform(): Platform {
  // Server-side rendering check
  if (typeof window === 'undefined' || typeof navigator === 'undefined') {
    return 'unknown';
  }
  
  const userAgent = navigator.userAgent || navigator.vendor || (window as any).opera || '';
  
  // Check for iOS devices
  if (/iPad|iPhone|iPod/.test(userAgent) && !(window as any).MSStream) {
    return 'ios';
  }
  
  // Check for Android devices
  if (/android/i.test(userAgent)) {
    return 'android';
  }
  
  // Default to web for desktop browsers
  return 'web';
}

/**
 * Check if the current device is mobile (iOS or Android)
 * 
 * @returns boolean indicating if device is mobile
 */
export function isMobile(): boolean {
  const platform = detectPlatform();
  return platform === 'ios' || platform === 'android';
}

/**
 * Add platform parameter to a URL
 * 
 * @param url URL to add platform parameter to
 * @returns URL with platform parameter added
 */
export function addPlatformToUrl(url: string): string {
  const platform = detectPlatform();
  
  // Only add platform if it's mobile
  if (platform === 'web' || platform === 'unknown') {
    return url;
  }
  
  // Add platform parameter
  const separator = url.includes('?') ? '&' : '?';
  return `${url}${separator}platform=${platform}`;
}