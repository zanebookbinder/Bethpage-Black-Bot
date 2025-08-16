import { View } from "@aws-amplify/ui-react"

export default function TabWrapper({component}) {
	return (
		<View 
			className="tab-wrapper"
		>
			{component}
		</View>
	);
}