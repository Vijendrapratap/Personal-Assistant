import React, { useState, useCallback, useEffect } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { GiftedChat, IMessage } from 'react-native-gifted-chat';
import client from '../api/client';

export default function ChatScreen() {
    const [messages, setMessages] = useState<IMessage[]>([]);

    useEffect(() => {
        setMessages([
            {
                _id: 1,
                text: 'Hello sir, how may I assist you today?',
                createdAt: new Date(),
                user: {
                    _id: 2,
                    name: 'Alfred',
                    avatar: 'https://placeimg.com/140/140/any',
                },
            },
        ]);
    }, []);

    const onSend = useCallback(async (newMessages: IMessage[] = []) => {
        setMessages((previousMessages) => GiftedChat.append(previousMessages, newMessages));

        const userMessage = newMessages[0].text;

        try {
            // Call Backend
            const response = await client.post('/chat', { message: userMessage });
            const botResponse = response.data.response;

            const botMessage: IMessage = {
                _id: Math.round(Math.random() * 1000000),
                text: botResponse,
                createdAt: new Date(),
                user: {
                    _id: 2,
                    name: 'Alfred',
                    avatar: 'https://placeimg.com/140/140/any',
                },
            };

            setMessages((previousMessages) => GiftedChat.append(previousMessages, [botMessage]));
        } catch (error) {
            console.error(error);
            Alert.alert("Error", "Alfred is having trouble connecting.");
        }
    }, []);

    return (
        <View style={styles.container}>
            <GiftedChat
                messages={messages}
                onSend={(messages) => onSend(messages)}
                user={{
                    _id: 1,
                }}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#fff' },
});
