// lib/api-client.ts - IPC-based API client

export async function getInbox(params = {}) {
  if (typeof window === 'undefined' || !(window as any).electronAPI) {
    throw new Error('API client only available in Electron');
  }
  
  return (window as any).electronAPI.apiGetInbox(params);
}

export async function getCaptureById(captureId: string) {
  if (typeof window === 'undefined' || !(window as any).electronAPI) {
    throw new Error('API client only available in Electron');
  }
  
  return (window as any).electronAPI.apiGetCaptureById(captureId);
}

export async function askAboutCapture(captureId: string, question: string) {
  if (typeof window === 'undefined' || !(window as any).electronAPI) {
    throw new Error('API client only available in Electron');
  }
  
  return (window as any).electronAPI.apiAskCapture(captureId, question);
}

export async function getCollections() {
  if (typeof window === 'undefined' || !(window as any).electronAPI) {
    throw new Error('API client only available in Electron');
  }
  
  return (window as any).electronAPI.apiGetCollections();
}

export async function getThemeClusters(numClusters: number = 4) {
  if (typeof window === 'undefined' || !(window as any).electronAPI) {
    throw new Error('API client only available in Electron');
  }
  
  return (window as any).electronAPI.apiGetThemeClusters(numClusters);
}

export async function askQuestion(question: string, filterDomain?: string) {
  if (typeof window === 'undefined' || !(window as any).electronAPI) {
    throw new Error('API client only available in Electron');
  }
  
  return (window as any).electronAPI.apiAskQuestion(question, filterDomain);
}