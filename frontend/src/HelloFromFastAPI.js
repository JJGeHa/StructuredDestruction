import React, { useEffect, useState } from 'react';
import { API_BASE } from './api';

function HelloFromFastAPI() {
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/hello`)
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch(() => setMessage('Error fetching from backend'));
  }, []);

  return (
    <div>
      <h3>Backend says:</h3>
      <p>{message}</p>
    </div>
  );
}

export default HelloFromFastAPI;
