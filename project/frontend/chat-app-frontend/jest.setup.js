// jest.setup.js
import '@testing-library/jest-dom';

// Mock scrollIntoView as it's not implemented in JSDOM and can cause errors.
if (typeof window !== 'undefined' && window.HTMLElement) {
  window.HTMLElement.prototype.scrollIntoView = jest.fn();
} else {
  // Fallback for environments where HTMLElement might not be fully available initially
  // or handle more gracefully. For typical jest-environment-jsdom, this else might not be strictly needed.
  const mockHTMLElement = {
    prototype: {
      scrollIntoView: jest.fn(),
    },
  };
  global.HTMLElement = global.HTMLElement || mockHTMLElement;
}


// You can add other global setup here, e.g. mock server setup for MSW
