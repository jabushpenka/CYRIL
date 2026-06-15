import { useState, useEffect } from 'react'; 
import styles from './stylesheet/App.module.css';

import vkLogo from './assets/vk.svg';
import maxLogo from './assets/max.svg';
import tgLogo from './assets/tg.svg';
import vkLogoSelected from './assets/vk_selected.svg';
import maxLogoSelected from './assets/max_selected.svg';
import tgLogoSelected from './assets/tg_selected.svg';

export default function App() {
  // Состояния для данных из API
  const [groups, setGroups] = useState([]);
  const [chats, setChats] = useState([]);
  const [messages, setMessages] = useState([]);
  
  // Состояния для интерфейса
  const [activeGroupIndex, setActiveGroupIndex] = useState(0);
  const [activeChatId, setActiveChatId] = useState(null);
  
  // Состояния загрузки и ошибок
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        
        const groupsResponse = await fetch('http://92.63.102.203:8000/groups');
        const chatsResponse = await fetch('http://92.63.102.203:8000/chats');
        const messagesResponse = await fetch('http://92.63.102.203:8000/messages?skip=0&limit=999');

        if (!groupsResponse.ok || !chatsResponse.ok || !messagesResponse.ok) {
          throw new Error('Ошибка при загрузке данных с сервера');
        }

        const groupsData = await groupsResponse.json();
        const chatsData = await chatsResponse.json();
        const messagesData = await messagesResponse.json();

        // Обновляем оба состояния ОДНОВРЕМЕННО
        setGroups(groupsData);
        setChats(chatsData);
        setMessages(messagesData);

        console.log(messagesData);

        if (groupsData.length > 0 && chatsData.length > 0) {
          const firstGroupId = groupsData[0].group_id;
          const firstChatOfFirstGroup = chatsData.find(c => c.group_id === firstGroupId);
          
          if (firstChatOfFirstGroup) {
            setActiveChatId(firstChatOfFirstGroup.chat_id);
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const currentGroup = groups[activeGroupIndex];

  const filteredChats = chats.filter(chat => {
    if (!currentGroup) return false;
    return chat.group_id === currentGroup.group_id;
  });

  const activeChat = chats.find((chat) => chat.chat_id === activeChatId);

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.spinner}></div>
        <p>Загрузка интерфейса мессенджера...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <h3>⚠️ Произошла ошибка</h3>
        <p>{error}</p>
        <button onClick={() => window.location.reload()} className={styles.retryButton}>
          Повторить попытку
        </button>
      </div>
    );
  }

  const getMessengerType = (messengerId) => {
    switch (messengerId) {
      case 1: return 'tg'; 
      case 2: return 'max'; 
      case 3: return 'vk'; 
      default: return 'tg';
    }
  };

  return (
    <div className={styles.appContainer}>
      {/* Левая панель (Группы) */}
      <aside className={styles.folderSidebar}>
        {groups.map((group, index) => (
          <div 
            key={group.group_id}
            className={`${styles.folderItem} ${index === activeGroupIndex ? styles.folderActive : ''}`}
            onClick={() => {
              setActiveGroupIndex(index);

              setActiveChatId(null); 
            }}
          >
            {group.group_name} 
          </div>
        ))}
      </aside>

      {/* Средняя панель (Список чатов в выбранной группе) */}
      <aside className={styles.chatsSidebar}>
        {filteredChats.map((chat) => {
          const msgType = getMessengerType(chat.messenger_id);
          return (
            <div 
              key={chat.chat_id_in_messenger} 
              className={`${styles.chatItem} ${chat.chat_id === activeChatId ? styles.chatActive : ''}`}
              onClick={() => setActiveChatId(chat.chat_id)}
            >
              <div className={styles.chatIcon}>
                {msgType === 'tg' && <img src={tgLogo}/>}
                {msgType === 'max' && <img src={maxLogo}/>}
                {msgType === 'vk' && <img src={vkLogo}/>}
              </div>
              <span className={styles.chatName}>ID: {chat.chat_id_in_messenger}</span>
            </div>
          );
        })}
        
        {filteredChats.length === 0 && (
          <div className={styles.emptyText}>В этой группе нет чатов</div>
        )}
      </aside>

      {/* Правая панель (Окно чата) */}
      <main className={styles.chatWindow}>
        {activeChat ? (
          <>
            <header className={styles.chatHeader}>
              <div className={styles.chatHeaderIcon}>
                {getMessengerType(activeChat.messenger_id) === 'tg' && <img src={tgLogo}/>}
                {getMessengerType(activeChat.messenger_id) === 'max' && <img src={maxLogo}/>}
                {getMessengerType(activeChat.messenger_id) === 'vk' && <img src={vkLogo}/>}
              </div>
              <h2>Чат {activeChat.chat_id_in_messenger}</h2>
            </header>

            {/* Область сообщений */}
            <div className={styles.messagesContainer}>
              {messages.length > 0 ? (
                messages.map((msg) => {
                  if (msg.chat_id === activeChatId){
                  return(
                    <div key={msg.message_id_in_chat} className={styles.messageBubble}>
                      <div className={styles.messageSender}>
                        {msg.sender_name || msg.sender || 'Пользователь'}
                      </div>
                      {/* Текст сообщения */}
                      <div className={styles.messageText}>{msg.text}</div>
                    </div>
                  )}
                }
                )
              ) : (
                <div className={styles.noMessages}>
                  История сообщений пуста. Напишите что-нибудь!
                </div>
              )}
            </div>

            {/* Поле ввода */}
            <footer className={styles.inputArea}>
              <div className={styles.inputWrapper}>
                <input 
                  type="text" 
                  placeholder="две конфеты чокопай" 
                  className={styles.messageInput} 
                />
              </div>
              <button className={styles.sendButton}>
                <span>1</span>
              </button>
            </footer>
          </>
        ) : (
          <div className={styles.emptyChatWindow}>
            <p>Выберите чат, чтобы начать общение</p>
          </div>
        )}
      </main>

    </div>
  );
}