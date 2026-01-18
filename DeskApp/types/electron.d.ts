export interface ElectronAPI {
  captureScreen: () => Promise<{
    success: boolean;
    screenshot?: string;
    timestamp?: number;
    windowContext?: {
      title: string;
      app: string;
    };
    error?: string;
  }>;
  onScreenshotCaptured: (callback: (data: any) => void) => void;
}

declare global {
  interface Window {
    electron: ElectronAPI;
  }
}