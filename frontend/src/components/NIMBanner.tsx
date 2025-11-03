export function NIMBanner() {
  return (
    <div style={{
      backgroundColor: '#76b900',
      color: '#ffffff',
      padding: '12px 20px',
      textAlign: 'center',
      fontWeight: 500,
      fontSize: '14px',
      borderBottom: '1px solid #5a8f00',
      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
      width: '100%',
    }}>
      <span style={{ marginRight: '8px' }}>ⓘ</span>
      This demo instance uses <strong>NVIDIA-hosted NIMs</strong> (not AWS-hosted) for easy public access
    </div>
  );
}
