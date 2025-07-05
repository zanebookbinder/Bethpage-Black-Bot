import { View } from "@aws-amplify/ui-react"

export default function TabWrapper({component}) {
	return (
		<View 
			width="500px" 
			backgroundColor="white"
			boxShadow="0px 4px 12px rgba(0, 0, 0, 0.1)"
			borderRadius="1rem"
			marginTop="1rem"
			padding="2rem"
			marginInline={"auto"}
		>
			{component}
		</View>
	);
}