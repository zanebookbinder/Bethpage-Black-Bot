import { View } from "@aws-amplify/ui-react"

export default function TabWrapper({component}) {
	return (
		<View 
			maxWidth="650px"
			backgroundColor="#e9e6cc"
			borderRadius="1rem"
			margin="1rem"
			padding="2rem"
			marginInline={"auto"}
		>
			{component}
		</View>
	);
}