import { DefineSkill } from '@mariozechner/pi-agent-core';

/**
 * Native RAE Bridge Skill for OpenClaw.
 * Implements Phase 3 Hard Frames (Semantic Firewall) and A2A Interaction.
 */
export default DefineSkill({
  name: 'rae-bridge',
  description: 'Enterprise Bridge for RAE Suite. Handles Phase 3 Audit and A2A Communication.',
  
  tools: {
    rae_bridge_audit: {
      description: 'Performs a Phase 3 Semantic Audit on a prompt before execution. Required for Hard Frames compliance.',
      inputSchema: {
        type: 'object',
        properties: {
          prompt: { type: 'string', description: 'The text prompt to audit' },
          context: { type: 'string', description: 'Operational context (e.g. project name)' }
        },
        required: ['prompt']
      },
      async run({ prompt, context }) {
        const raeUrl = process.env.RAE_API_URL || 'http://rae-api-dev:8000';
        try {
          const response = await fetch(`${raeUrl}/v2/bridge/audit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt, context, source_agent: 'open-claw' })
          });
          
          if (!response.ok) {
            const error = await response.json();
            throw new Error(`Semantic Firewall Blocked: ${error.detail || 'Unknown reason'}`);
          }
          
          return await response.json();
        } catch (e) {
          return { status: 'rejected', reason: e.message };
        }
      }
    },
    
    rae_bridge_interact: {
      description: 'Sends an A2A message to another RAE Agent through the Bridge.',
      inputSchema: {
        type: 'object',
        properties: {
          target_agent: { type: 'string', description: 'Destination agent (e.g. rae-quality, rae-phoenix)' },
          payload: { type: 'object', description: 'JSON data to send' },
          session_id: { type: 'string' }
        },
        required: ['target_agent', 'payload']
      },
      async run({ target_agent, payload, session_id }) {
        const raeUrl = process.env.RAE_API_URL || 'http://rae-api-dev:8000';
        const response = await fetch(`${raeUrl}/v2/bridge/interact`, {
          method: 'POST',
          headers: { 
            'Content-Type': 'application/json',
            'X-Tenant-Id': '00000000-0000-0000-0000-000000000000',
            'X-Project-Id': 'dreamsoft_factory'
          },
          body: JSON.stringify({
            payload,
            source_agent: 'open-claw',
            target_agent,
            session_id
          })
        });
        return await response.json();
      }
    }
  }
});
