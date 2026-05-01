/**
 * Centralized error handling utilities
 * Maps backend error codes to user-friendly messages
 */

export interface ApiError {
  code: string;
  message: string;
  details?: any;
  statusCode?: number;
}

export class AppError extends Error {
  constructor(
    public code: string,
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'AppError';
  }
}

/**
 * Error code mappings to user-friendly messages
 */
const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  'NETWORK_ERROR': 'Unable to connect to the server. Please check your internet connection.',
  'TIMEOUT': 'The request took too long. Please try again.',
  'OFFLINE': 'You are currently offline. Please check your internet connection.',
  
  // Authentication errors
  'UNAUTHORIZED': 'You are not authorized to perform this action. Please log in.',
  'FORBIDDEN': 'You do not have permission to access this resource.',
  'INVALID_TOKEN': 'Your session has expired. Please log in again.',
  
  // Validation errors
  'INVALID_ADDRESS': 'The wallet address is invalid. Please check and try again.',
  'INVALID_SCORE': 'The credit score value is invalid.',
  'INVALID_RISK_BAND': 'The risk band value is invalid.',
  'MISSING_FIELDS': 'Please fill in all required fields.',
  
  // Blockchain errors
  'BLOCKCHAIN_ERROR': 'There was an error interacting with the blockchain. Please try again.',
  'TRANSACTION_FAILED': 'The transaction failed. Please check your wallet and try again.',
  'INSUFFICIENT_GAS': 'You do not have enough gas to complete this transaction.',
  'WALLET_NOT_CONNECTED': 'Please connect your wallet to continue.',
  'CONTRACT_ERROR': 'There was an error with the smart contract. Please try again later.',
  
  // API errors
  'RATE_LIMIT_EXCEEDED': 'Too many requests. Please wait a moment and try again.',
  'SERVICE_UNAVAILABLE': 'The service is temporarily unavailable. Please try again later.',
  'INTERNAL_ERROR': 'An unexpected error occurred. Our team has been notified.',
  
  // Scoring errors
  'SCORE_GENERATION_FAILED': 'Failed to generate credit score. Please try again.',
  'SCORE_NOT_FOUND': 'Credit score not found for this address.',
  'INSUFFICIENT_DATA': 'Not enough data available to generate a credit score.',
  
  // Loan errors
  'LOAN_NOT_FOUND': 'Loan not found.',
  'LOAN_ALREADY_EXISTS': 'A loan with this ID already exists.',
  'INSUFFICIENT_COLLATERAL': 'Insufficient collateral for this loan.',
  'LOAN_DEFAULTED': 'This loan has been defaulted.',
  
  // Staking errors
  'STAKING_FAILED': 'Staking operation failed. Please try again.',
  'INSUFFICIENT_BALANCE': 'You do not have enough tokens to complete this action.',
  'UNSTAKE_FAILED': 'Unstaking operation failed. Please try again.',
  
  // Default
  'UNKNOWN_ERROR': 'An unexpected error occurred. Please try again or contact support.',
};

/**
 * Extract error message from various error formats
 */
export function extractErrorMessage(error: unknown): string {
  if (error instanceof AppError) {
    return error.message;
  }
  
  if (error instanceof Error) {
    // Check if it's an API error with a code
    const apiError = error as any;
    if (apiError.code && ERROR_MESSAGES[apiError.code]) {
      return ERROR_MESSAGES[apiError.code];
    }
    
    // Check if error message contains a known code
    for (const [code, message] of Object.entries(ERROR_MESSAGES)) {
      if (error.message.includes(code)) {
        return message;
      }
    }
    
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  if (error && typeof error === 'object') {
    const err = error as any;
    
    // Check for API error response format
    if (err.response?.data?.message) {
      return err.response.data.message;
    }
    
    if (err.response?.data?.detail) {
      return err.response.data.detail;
    }
    
    if (err.message) {
      return err.message;
    }
    
    if (err.code && ERROR_MESSAGES[err.code]) {
      return ERROR_MESSAGES[err.code];
    }
  }
  
  return ERROR_MESSAGES['UNKNOWN_ERROR'];
}

/**
 * Extract error code from error
 */
export function extractErrorCode(error: unknown): string {
  if (error instanceof AppError) {
    return error.code;
  }
  
  if (error && typeof error === 'object') {
    const err = error as any;
    
    if (err.code) {
      return err.code;
    }
    
    if (err.response?.data?.code) {
      return err.response.data.code;
    }
  }
  
  return 'UNKNOWN_ERROR';
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  const code = extractErrorCode(error);
  return ['NETWORK_ERROR', 'TIMEOUT', 'OFFLINE'].includes(code);
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: unknown): boolean {
  const code = extractErrorCode(error);
  return [
    'NETWORK_ERROR',
    'TIMEOUT',
    'SERVICE_UNAVAILABLE',
    'INTERNAL_ERROR',
    'RATE_LIMIT_EXCEEDED',
  ].includes(code);
}

/**
 * Format error for display
 */
export function formatError(error: unknown): ApiError {
  return {
    code: extractErrorCode(error),
    message: extractErrorMessage(error),
    statusCode: error instanceof AppError ? error.statusCode : undefined,
    details: error && typeof error === 'object' ? (error as any).details : undefined,
  };
}

/**
 * Handle API response errors
 */
export async function handleApiError(response: Response): Promise<never> {
  let errorData: any;
  
  try {
    errorData = await response.json();
  } catch {
    errorData = { message: response.statusText };
  }
  
  const code = errorData.code || `HTTP_${response.status}`;
  const message = errorData.message || errorData.detail || ERROR_MESSAGES[code] || `Error ${response.status}`;
  
  throw new AppError(code, message, response.status, errorData);
}

