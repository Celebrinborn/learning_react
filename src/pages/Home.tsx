import { makeStyles, tokens, Title1, Text } from '@fluentui/react-components';

const useStyles = makeStyles({
  container: {
    padding: tokens.spacingHorizontalXXL,
  },
});

export default function Home() {
  const styles = useStyles();

  return (
    <div className={styles.container}>
      <Title1>D&D Stats Sheet</Title1>
      <Text>Welcome to your D&D character management system!</Text>
    </div>
  );
}
