import './App.css';
import {Amplify} from 'aws-amplify';
import { Authenticator, withAuthenticator } from '@aws-amplify/ui-react';
import '@aws-amplify/ui-react/styles.css';
import awsExports from './aws-exports';

Amplify.configure(awsExports);


function App() {
  return (
    <div className="w-full h-full flex flex-col bg-gradient-to-r from-indigo-500 from-10% via-sky-500 via-30% to-emerald-500 to-90%">
      <Authenticator>
        {({ signOut }) => (
          <main className="flex flex-col flex-grow">
            <header className="flex justify-between items-center p-4">
              <div></div>
              <button 
                onClick={signOut} 
                className="bg-white hover:bg-blue-700 hover:text-white text-blue-500 font-bold py-2 px-4 rounded"
              >
                Sign Out
              </button>
            </header>
            <div className="flex-grow">
              {/* Quiz Component */}
              {/* <Quiz /> */}
            </div>
          </main>
        )}
      </Authenticator>
    </div>
  );
}

export default withAuthenticator(App);