import React from 'react';
import {Button, StyleSheet, Text, View, TextInput} from 'react-native';
import {styles} from "../App";
import RankingStar from "../components/RankingStar";

export class CreateGameInfo extends React.Component {
  static navigationOptions = {
    title: 'Game Info',
    headerStyle: {
      height: 50,
      backgroundColor: '#77b2ff',
    },
    headerTitleStyle: {
      fontWeight: 'bold',
    },
  };

  render() {
    return (
      <View style={styles.screen}>
        <View style={styles.homeHeader}>
          <Text style={styles.headerText}>
            Game Title
          </Text>
        </View>
        <View style ={{padding: 5}}>
        <TextInput
          style={{
            borderColor: '#000000',
            borderWidth: 1,
          }}
          placeholder=" Enter title "
          // onSubmitEditing = {(text) => this.setState({text})}
          // onChangeText={(text) => this.setState({text})}
        />
        </View>
        <View style={styles.homeHeader}>
          <Text style={styles.headerText}>
            Game Description
          </Text>
        </View>
        <View style ={{padding: 5}}>
        <TextInput
          style={{
            borderColor: '#000000',
            borderWidth: 1,
          }}
          placeholder=" Enter Description "

          multiline={true}
          numberOfLines={8}
          // onChangeText={(text) => this.setState({text})}
        />
        </View>
        <View style={styles.homeHeader}>
          <Text style={styles.headerText}>
            Set Competitive Level
          </Text>
        </View>
        <View style={styles.container}>
          <RankingStar/>
        </View>
        <View style={{flex: 5}}/>
        <View style={styles.nextButton}>
          <Button
            title="Next"
            color="#fff"
            onPress={() => this.props.navigation.navigate('Home')}
          />
        </View>
      </View>
    );
  }
}