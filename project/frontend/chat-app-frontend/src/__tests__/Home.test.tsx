// src/__tests__/Home.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import Home from '@/app/page'; // Assuming default export from src/app/page.tsx

// Mock socket.io-client if it's used directly in Home and causes issues during rendering in test
// jest.mock('socket.io-client', () => ({
//   io: jest.fn(() => ({
//     on: jest.fn(),
//     off: jest.fn(),
//     emit: jest.fn(),
//     connect: jest.fn(),
//     disconnect: jest.fn(),
//     connected: true, // or false, depending on what you want to mock
//     id: 'mockSocketId'
//   })),
// }));


describe('Home Page', () => {
  it('renders a heading (example)', async () => {
    // If Home is an async component, or fetches data, this might need adjustment
    render(<Home />);
    // Look for a common element, like a heading or main landmark
    // This is a placeholder, actual content will vary.
    // Try to find something that is likely to be there.
    // For instance, if there's a <h1> with "Chat Application"
    // const heading = await screen.findByRole('heading', { name: /Chat Application/i });
    // expect(heading).toBeInTheDocument();

    // For now, a very basic check:
    // Check if the main landmark is rendered, Next.js app router pages often have one.
    const mainElement = screen.getByRole('main');
    expect(mainElement).toBeInTheDocument();
  });
});
