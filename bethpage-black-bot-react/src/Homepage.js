import React, { useState } from 'react';
import { Tabs } from '@aws-amplify/ui-react';
import CurrentTeeTimes from './components/CurrentTeeTimes';
import UpdateConfiguration from './components/UpdateConfiguration';
import SignUpMenu from './components/SignUpMenu';

export default function Homepage() {
  const [activeTab, setActiveTab] = useState('home');

  return (
    <div style={{ maxWidth: 600, margin: 'auto', padding: 20 }}>
      <h1>Bethpage Black Bot</h1>

      <Tabs
        justifyContent="flex-start"
        defaultValue='Tab 1'
        items={[
          { label: 'Bethpage Black tee times', value: 'Bethpage Black tee times', content: <CurrentTeeTimes /> },
          { label: 'Sign up', value: 'Sign up', content: <SignUpMenu /> },
          { label: 'Update configuration', value: 'Update configuration', content: <UpdateConfiguration /> },
        ]}
      />
  </div>
  );
}
