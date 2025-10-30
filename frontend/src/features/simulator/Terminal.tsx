import { useEffect, useRef } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import type { RootState, AppDispatch } from '../../app/store';
import { addCLIHistoryEntry } from './simulatorSlice';
import '@xterm/xterm/css/xterm.css';
import './Terminal.css';

export type CLITrigger = 'enter' | 'tab' | 'question' | 'up_arrow' | 'down_arrow';

interface TerminalProps {
  deviceId: string;
  onCommand: (text: string, trigger: CLITrigger) => void;
  isActive: boolean;
}

export const Terminal: React.FC<TerminalProps> = ({ deviceId, onCommand, isActive }) => {
  const dispatch = useDispatch<AppDispatch>();
  const terminalRef = useRef<HTMLDivElement>(null);
  const xtermRef = useRef<XTerm | null>(null);
  const fitAddonRef = useRef<FitAddon | null>(null);
  const currentLineRef = useRef<string>('');
  const lastSequenceRef = useRef<number>(0);
  const lastTriggerRef = useRef<CLITrigger>('enter');
  const lastCommandRef = useRef<string>('');

  // Read CLI state for the specific device
  const deviceState = useSelector((state: RootState) => state.simulator.deviceStates[deviceId]);
  const { output, prompt, current_input, sequence } = deviceState || {
    output: '',
    prompt: '',
    current_input: '',
    sequence: 0,
  };
  const status = useSelector((state: RootState) => state.simulator.connectionStatus);
  const error = useSelector((state: RootState) => state.simulator.lastError);

  // Initialize terminal
  useEffect(() => {
    if (!deviceId || !terminalRef.current) {
      return;
    }

    // Skip if terminal already initialized (we keep terminals mounted now)
    if (xtermRef.current) {
      return;
    }

    // Initialize xterm.js
    const term = new XTerm({
      cursorBlink: true,
      cursorStyle: 'bar',
      theme: {
        background: '#1e1e1e',
        foreground: '#00ff00',
      },
      fontSize: 14,
      fontFamily: 'Courier New, courier, monospace',
      lineHeight: 1.2,
    });

    // Initialize FitAddon
    const fitAddon = new FitAddon();
    term.loadAddon(fitAddon);
    fitAddonRef.current = fitAddon;

    try {
      term.open(terminalRef.current);
      xtermRef.current = term;

      // Fit the terminal to its container
      fitAddon.fit();

      // Handle user input
      term.onData((data: string) => {
        if (!deviceId) return; // Ignore input if no device selected

        switch (data) {
          case '\r': // Enter
            console.log('[Terminal:onData] Enter pressed, current line:', currentLineRef.current);
            lastTriggerRef.current = 'enter';
            lastCommandRef.current = currentLineRef.current; // Store command for history
            onCommand(currentLineRef.current, 'enter');
            currentLineRef.current = '';
            break;

          case '\u007F': // Backspace
            if (currentLineRef.current.length > 0) {
              term.write('\b \b');
              currentLineRef.current = currentLineRef.current.slice(0, -1);
              console.log('[Terminal:onData] Backspace pressed, current line:', currentLineRef.current);
            }
            break;

          case '\t': // Tab
            console.log('[Terminal:onData] Tab pressed, current line:', currentLineRef.current);
            lastTriggerRef.current = 'tab';
            onCommand(currentLineRef.current, 'tab');
            break;

          case '?':
            console.log('[Terminal:onData] Question mark pressed, current line:', currentLineRef.current);
            term.write('?');
            currentLineRef.current += '?';
            lastTriggerRef.current = 'question';
            onCommand(currentLineRef.current, 'question');
            currentLineRef.current = '';
            break;

          case '\x1b[A': // Up arrow
            console.log('[Terminal:onData] Up arrow pressed');
            lastTriggerRef.current = 'up_arrow';
            onCommand(currentLineRef.current, 'up_arrow');
            break;

          case '\x1b[B': // Down arrow
            console.log('[Terminal:onData] Down arrow pressed');
            lastTriggerRef.current = 'down_arrow';
            onCommand(currentLineRef.current, 'down_arrow');
            break;

          default:
            if (data >= ' ' && data <= '~') { // Printable characters
              term.write(data);
              currentLineRef.current += data;
              console.log('[Terminal:onData] Character typed, current line:', currentLineRef.current);
            }
        }
      });

      // Handle window resize
      const handleResize = () => {
        if (fitAddonRef.current) {
          fitAddonRef.current.fit();
        }
      };

      window.addEventListener('resize', handleResize);
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    } catch (error) {
      console.error('Error initializing terminal:', error);
    }
  }, [deviceId, onCommand]);

  // Handle output changes
  useEffect(() => {
    if (xtermRef.current) {
      if (!deviceId) {
        xtermRef.current.clear();
        xtermRef.current.write('Please select a device to begin...\r\n');
        return;
      }

      // Only process if sequence has changed
      if (sequence !== lastSequenceRef.current) {
        console.log('[Terminal:output] Processing new output:', {
          sequence,
          lastSequence: lastSequenceRef.current,
          output,
          trigger: lastTriggerRef.current,
          currentLine: currentLineRef.current,
        });

        lastSequenceRef.current = sequence;

        // Handle output if present
        if (output !== undefined) {
          const outputStr = typeof output === 'object' ? JSON.stringify(output, null, 2) : output;

          console.log('[Terminal:output] Processing output string:', {
            outputStr,
            trigger: lastTriggerRef.current,
            currentLine: currentLineRef.current,
            current_input,
          });

          // Handle output based on trigger type
          if (lastTriggerRef.current === 'tab') {
            console.log('[Terminal:output:tab] Writing tab completion');
            xtermRef.current.write('\r\n');
            xtermRef.current.write(prompt);
            xtermRef.current.write(outputStr);
            currentLineRef.current = outputStr;
          } else if (lastTriggerRef.current === 'enter') {
            console.log('[Terminal:output:enter] Writing enter response');
            xtermRef.current.write('\r\n');
            if (outputStr) {
              const lines = outputStr.split(/\n/);
              for (const line of lines) {
                xtermRef.current.write(line + '\r\n');
              }
            }
          } else if (lastTriggerRef.current === 'up_arrow' || lastTriggerRef.current === 'down_arrow') {
            console.log('[Terminal:output:arrows] Writing history navigation');
            const currentLength = currentLineRef.current.length;
            xtermRef.current.write('\r');
            xtermRef.current.write(' '.repeat(prompt.length + currentLength));
            xtermRef.current.write('\r');
            xtermRef.current.write(prompt);
            currentLineRef.current = current_input || '';
            if (current_input) {
              xtermRef.current.write(current_input);
            }
          } else if (lastTriggerRef.current === 'question') {
            console.log('[Terminal:output:question] Writing help output');
            // Add newline before help output to move to next line
            xtermRef.current.write('\r\n');
            if (outputStr) {
              const lines = outputStr.split(/\n/);
              for (const line of lines) {
                xtermRef.current.write(line + '\r\n');
              }
            }
          } else if (outputStr && outputStr.trim()) {
            // For other triggers, write the output
            const lines = outputStr.split(/\n/);
            for (const line of lines) {
              if (line.trim()) {
                xtermRef.current.write(line + '\r\n');
              }
            }
          }

          // Add to CLI history (only for 'enter' commands with actual command text)
          if (lastTriggerRef.current === 'enter' && lastCommandRef.current) {
            dispatch(addCLIHistoryEntry({
              command: lastCommandRef.current,
              output: outputStr || '',
              timestamp: new Date().toISOString(),
              device_id: deviceId,
            }));
            lastCommandRef.current = ''; // Clear after recording
          }
        }

        // Write the prompt after output (except for special cases)
        if (prompt && lastTriggerRef.current !== 'tab' &&
            lastTriggerRef.current !== 'up_arrow' &&
            lastTriggerRef.current !== 'down_arrow') {
          console.log('[Terminal:output:final] Writing final prompt');
          xtermRef.current.write(prompt);

          if (current_input) {
            console.log('[Terminal:output:final] Writing current_input:', current_input);
            xtermRef.current.write(current_input);
            currentLineRef.current = current_input;
          }
        }
      }

      // Handle errors
      if (error) {
        console.log('[Terminal:output] Processing error:', error);
        const errorLines = error.split(/\n/);
        for (const line of errorLines) {
          if (line.trim()) {
            xtermRef.current.write(`\r\nError: ${line}\r\n`);
          }
        }
        xtermRef.current.write(prompt);
      }
    }
  }, [output, prompt, error, deviceId, sequence, current_input]);

  // Auto-focus terminal when it becomes active
  useEffect(() => {
    if (isActive && xtermRef.current) {
      xtermRef.current.focus();
    }
  }, [isActive]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (xtermRef.current) {
        xtermRef.current.dispose();
        xtermRef.current = null;
        fitAddonRef.current = null;
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-full">
      {/* Status bar */}
      <div className="flex justify-between text-xs p-2 bg-gray-800 text-gray-300 border-b border-gray-700">
        <span>Device: {deviceId || 'None'}</span>
        <span className={`${
          status === 'connected' ? 'text-green-500' :
          status === 'connecting' ? 'text-yellow-500' :
          status === 'reconnecting' ? 'text-orange-500' :
          'text-red-500'
        }`}>
          {status}
        </span>
      </div>

      {/* Terminal */}
      <div ref={terminalRef} className="flex-1 min-h-0" />
    </div>
  );
};
