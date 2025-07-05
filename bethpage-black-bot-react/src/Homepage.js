import { View, Tabs, Heading } from '@aws-amplify/ui-react';
import CurrentTeeTimes from './components/CurrentTeeTimes';
import SignUpMenu from './components/SignUpMenu';
import TabWrapper from './TabWrapper';
import GetOneTimeLink from './components/GetOneTimeLink';

export default function Homepage() {

  return (
    <div style={{ maxWidth: 700, margin: 'auto', padding: 20, backgroundColor: "rgb(176, 208, 166)",
      boxShadow: "0px 4px 12px rgba(0,0,0,0.1)", borderRadius: "1rem"
     }}>
      <Heading level={2} fontWeight="medium" textAlign="center"> Bethpage Black Bot</Heading>

      <View display="flex" justifyContent="center" marginTop="1rem">
        <View>
          <Tabs
            defaultValue={'tee-times'}
            items={[
              { label: 'Current Tee Times', value: 'tee-times', content: <TabWrapper component={<CurrentTeeTimes />} /> },
              { label: 'Sign up', value: 'sign-up', content: <TabWrapper component={<SignUpMenu />} /> },
              { label: 'Update Your Notification Settings', value: 'update-notification-settings', content: <TabWrapper component={<GetOneTimeLink />} /> },
            ]}
          />
        </View>
    </View>
  </div>
  );
}
