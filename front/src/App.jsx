import { useState, useEffect, useRef } from 'react'; 
import styles from './stylesheet/App.module.css';

import vkLogo from './assets/vk.svg';
import maxLogo from './assets/max.svg';
import tgLogo from './assets/tg.svg';
import vkLogoSelected from './assets/vk_selected.svg';
import maxLogoSelected from './assets/max_selected.svg';
import tgLogoSelected from './assets/tg_selected.svg';
import backArrow from './assets/back_arrow.svg';

export default function App() {
  // данные из api
  const [groups, setGroups] = useState([]);
  const [chats, setChats] = useState([]);
  const [messages, setMessages] = useState([]);
  
  // для интерфейса главного меню
  const [activeGroupIndex, setActiveGroupIndex] = useState(0);
  const [activeChatId, setActiveChatId] = useState(null);
  
  // Состояние для отображения меню внутри Групп
  const [isGroupMenuOpen, setIsGroupMenuOpen] = useState(false);
  const [groupMenuStage, setGroupMenuStage] = useState(0); 
  const [inputGroupId, setInputGroupId] = useState(''); 
  const [inputGroupName, setInputGroupName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false); 
  const [menuError, setMenuError] = useState(null); 

  const [isChatMenuOpen, setIsChatMenuOpen] = useState(false);

  // загрузки/ошибки
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);


  const socketRef = useRef(null); // для вебсокет
  const messagesEndRef = useRef(null); // для автоскролла

  const currentGroup = groups[activeGroupIndex];

  // эффект вебсокета
  useEffect(() => {
    const ws = new WebSocket('ws://92.63.102.203:8000/ws');
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket успешно подключен');
      if (currentGroup) {
        ws.send(JSON.stringify({ action: 'add', group_id: currentGroup.group_id }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const newMessage = JSON.parse(event.data);
        console.log('Получено сообщение через WS:', newMessage);

        if (newMessage && newMessage.chat_id) {
          setMessages((prevMessages) => {
            const isDuplicate = prevMessages.some(
              (m) => m.message_id_in_chat === newMessage.message_id_in_chat && m.chat_id === newMessage.chat_id
            );

            if (isDuplicate) return prevMessages;
            return [...prevMessages, newMessage];
          });
        }
      } catch (err) {
        console.error('Ошибка обработки данных из WebSocket:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('Ошибка WebSocket:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket соединение закрыто');
    };

    // при размонтировании закрытие вс
    return () => {
      if (ws) ws.close();
    };
  }, []);

  // для переключения группы, которую слушаем в вебсокете
  useEffect(() => {
    const ws = socketRef.current;
    
    // КРИТИЧНО: Если сокет ещё не открылся, мы не можем вызвать ws.send().
    // Поэтому мы подстрахуемся и повесим отправку на событие onopen, 
    // если оно произойдет чуть позже, либо отправим сразу, если сокет уже готов.
    const subscribe = () => {
      if (ws && ws.readyState === WebSocket.OPEN && currentGroup) {
        console.log(`WS: Подписка на группу ${currentGroup.group_id}`);
        ws.send(JSON.stringify({
          action: 'add',
          group_id: currentGroup.group_id
        }));
      }
    };

    if (!ws) return;

    if (ws.readyState === WebSocket.OPEN) {
      subscribe();
    } else {
      //сокет в процессе подключения — ждем события open
      ws.addEventListener('open', subscribe);
    }

    // cleanup срабатывает ПЕРЕД следующим изменением группы
    return () => {
      if (ws) {
        // чтобы не дублировать слушатель
        ws.removeEventListener('open', subscribe);
        
        // отписка от старой группы
        if (ws.readyState === WebSocket.OPEN && currentGroup) {
          console.log(`WS: Отписка от группы ${currentGroup.group_id}`);
          ws.send(JSON.stringify({
            action: 'remove',
            group_id: currentGroup.group_id
          }));
        }
      }
    };
  }, [currentGroup?.group_id]);

  // подтягивание из localstorage групп
  useEffect(() => {
    const savedGroups = JSON.parse(localStorage.getItem('added_groups')) || [];
    setGroups(savedGroups);
    
    const initialLoadAllData = async () => {
      if (savedGroups.length === 0) return;
      try {
        setIsLoading(true);
        for (const group of savedGroups) {
          await fetchChatsAndMessagesForGroup(group.group_id);
        }
      } catch (err) {
        console.error("Ошибка при инициализации данных групп:", err);
      } finally {
        setIsLoading(false);
      }
    };
    
    initialLoadAllData();
  }, []);

  // автоскролл до конца в чате
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, activeChatId]);

  // вспомогательные функции
  // функция загрузки чатов и сообщений по groupId
  const fetchChatsAndMessagesForGroup = async (groupId) => {
    try {
      const responseChats = await fetch(`http://92.63.102.203:8000/group_get_chats?group_id=${parseInt(groupId, 10)}`);
      if (!responseChats.ok) return;
      
      const chatsNew = await responseChats.json();
      
      if (chatsNew && chatsNew.length !== 0) {
        const chatsWithGroup = chatsNew.map(chat => ({
          ...chat,
          group_id: groupId
        }));

        setChats(prevChats => {
          const filteredPrev = prevChats.filter(pc => !chatsWithGroup.some(nc => nc.chat_id === pc.chat_id));
          return [...filteredPrev, ...chatsWithGroup];
        });

        for (const chat of chatsWithGroup) {
          const responseMsgs = await fetch(`http://92.63.102.203:8000/chat_get_messages?chat_id=${encodeURIComponent(chat.chat_id)}`);
          if (responseMsgs.ok) {
            const messagesNew = await responseMsgs.json();
            if (messagesNew && messagesNew.length !== 0) {
              const messagesWithChat = messagesNew.map(message => ({
                ...message,
                chat_id: chat.chat_id
              }));
              
              setMessages(prevMessages => {
                const restMessages = prevMessages.filter(m => m.chat_id !== chat.chat_id);
                return [...restMessages, ...messagesWithChat];
              });
            }
          }
        }
      }
    } catch (err) {
      console.error("Ошибка запроса чатов/сообщений:", err);
    }
  };

  const filteredChats = chats.filter(chat => {
    if (!currentGroup) return false;
    return chat.group_id === currentGroup.group_id;
  });

  const activeChat = chats.find((chat) => chat.chat_id === activeChatId);

  // парс айди мессендежера в строку
  const getMessengerType = (messengerId) => {
    switch (messengerId) {
      case 1: return 'tg'; 
      case 2: return 'vk'; 
      case 3: return 'max'; 
      default: return 'vk';
    }
  };

  // подтягивание групп при добавлении по хешу
  const renderGroups = (groupData) => {
    const savedGroups = JSON.parse(localStorage.getItem('added_groups')) || [];
    const isAlreadyAdded = savedGroups.some(g => g.group_id === groupData.group_id);
    
    if (!isAlreadyAdded) {
      savedGroups.push(groupData);
      localStorage.setItem('added_groups', JSON.stringify(savedGroups));
      setGroups([...groups, groupData]);
    }

    setIsGroupMenuOpen(false);
    setInputGroupId('');
    setGroupMenuStage(0);
  };
  const handleAddExistingGroup = async () => {
    if (!inputGroupId.trim()) {
      setMenuError('Введите корректный ключ группы');
      return;
    }

    try {
      setIsSubmitting(true);
      setMenuError(null);

      const responseHash = await fetch(`http://92.63.102.203:8000/group_get_by_hashkey?hashkey=${encodeURIComponent(inputGroupId)}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!responseHash.ok) throw new Error('Данной группы не существует');

      const groupId = await responseHash.json();
      if (groupId === -1) throw new Error('Данной группы не существует');

      const responseName = await fetch(`http://92.63.102.203:8000/group_get_name?group_id=${parseInt(groupId, 10)}`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });
      const groupName = await responseName.json();

      const groupData = { group_id: groupId, group_name: groupName };

      await fetchChatsAndMessagesForGroup(groupId);

      // После добавления группы в массив, хук useEffect автоматически отправит WS-запрос на подписку
      renderGroups(groupData);

    } catch (err) {
      setMenuError('Ошибка! Данной группы не существует.');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Элементы интерфейса
  const groupHeader = () => {
    return (
      <div className={styles.groupsHeader}>
        {isGroupMenuOpen && groupMenuStage !== 0 ? (
          <div className={styles.headerBackContainer} onClick={() => setGroupMenuStage(0)}>
            <span className={styles.backArrow}><img src={backArrow} alt="Назад" /></span>
            <h3>{groupMenuStage === 1 ? "Добавить" : "Создать"}</h3>
          </div>
        ) : (
          <h3>Группы</h3>
        )}

        <button 
          className={`${styles.addButton} ${isGroupMenuOpen ? styles.minusButton : ''}`} 
          onClick={() => {
            setIsGroupMenuOpen(!isGroupMenuOpen);
            setGroupMenuStage(0); 
            setInputGroupId(''); 
            setMenuError(null);
          }}
        >
          <span>{isGroupMenuOpen ? '−' : '+'}</span>
        </button>
      </div>
    );
  };

  // пока убрал создание группы в интерфейсе
  const groupMenuStages = () => {
    if (groupMenuStage === 1) {
      return (
        <div className={styles.menuStageContainer}>
          <label className={styles.inputLabel}>Введите ключ группы:</label>
          <input 
            type="text" 
            placeholder="Key..." 
            className={styles.groupIdInput}
            value={inputGroupId}
            onChange={(e) => setInputGroupId(e.target.value)}
          />
          <button 
            className={styles.actionButton}
            onClick={handleAddExistingGroup}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Загрузка...' : 'Добавить'}
          </button>

          {menuError && (
            <div className={styles.errorText}>
              Ошибка!<br />Данной группы<br />не существует.
            </div>
          )}
        </div>
      );
    } else {
      return (
        <div className={styles.menuStageContainer}>
          <label className={styles.inputLabel}>Введите название группы:</label>
          <input 
            type="text" 
            placeholder="Название..." 
            className={styles.groupIdInput}
            value={inputGroupName}
            onChange={(e) => setInputGroupName(e.target.value)}
          />
          <button 
            className={styles.actionButton}
            onClick={() => console.log('Отправка названия новой группы:', inputGroupName)}
          >
            Добавить
          </button>
        </div>
      );
    }
  };

  //время сообщения + конвертация
  const messageTime = (msg) => {
    const date = new Date(msg.date);
    date.setHours(date.getHours() + 4);

    return (
    <div className={styles.messageTime}>
      {date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })}
    </div>)
  }

  // для актуализации данных при клике на чат ручным фетчем (на случай пропуска пакетов)
  // useEffect(() => {
  //   const fetchActiveChatMessages = async () => {
  //     if (activeChatId === null) return;
      
  //     try {
  //       const response = await fetch(`http://92.63.102.203:8000/chat_get_messages?chat_id=${encodeURIComponent(activeChatId)}`);
  //       if (!response.ok) return;
  //       const messagesNew = await response.json();

  //       if (messagesNew && messagesNew.length !== 0) {
  //         const messagesWithChat = messagesNew.map(message => ({
  //           ...message,
  //           chat_id: activeChatId
  //         }));
          
  //         setMessages(prevMessages => {
  //           const restMessages = prevMessages.filter(m => m.chat_id !== activeChatId);
  //           return [...restMessages, ...messagesWithChat];
  //         });
  //       }
  //     } catch (err) {
  //       console.error("Ошибка обновления сообщений активного чата:", err);
  //     }
  //   };

  //   fetchActiveChatMessages();
  // }, [activeChatId]);

  return (
    <div className={styles.appContainer}>
      {/* Левая панель (Группы) */}
      <aside className={styles.folderSidebar}>
        {groupHeader()}

        <div className={styles.sidebarContent}>
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

          {isGroupMenuOpen && (
            <div className={styles.groupActionOverlay}>
              {groupMenuStage === 0 ? (
                <div className={styles.menuStageContainer}>
                  <button className={styles.actionButton} onClick={() => setGroupMenuStage(1)}>
                    Добавить существующую
                  </button>
                </div>
              ) : (
                groupMenuStages()
              )}
            </div>
          )}
        </div>
      </aside>

      {/* Средняя панель (Список чатов) */}
      <aside className={styles.chatsSidebar}>
        <div className={styles.chatsHeader}>
          <h3>Чаты</h3>
        </div>

        <div className={styles.sidebarContent}>
          {filteredChats.map((chat) => {
            const msgType = getMessengerType(chat.messenger_id);
            return (
              <div 
                key={chat.chat_id_in_messenger} 
                className={`${styles.chatItem} ${chat.chat_id === activeChatId ? styles.chatActive : ''}`}
                onClick={() => setActiveChatId(chat.chat_id)}
              >
                <div className={styles.chatIcon}>
                  {msgType === 'tg' && <img src={tgLogo} alt="tg"/>}
                  {msgType === 'max' && <img src={maxLogo} alt="max"/>}
                  {msgType === 'vk' && <img src={vkLogo} alt="vk"/>}
                </div>
                <span className={styles.chatName}>ID: {chat.chat_id_in_messenger}</span>
              </div>
            );
          })}
          
          {filteredChats.length === 0 && (
            <div className={styles.emptyText}>В этой группе нет чатов</div>
          )}
        </div>
      </aside>

      {/* Правая панель (Окно чата) */}
      <main className={styles.chatWindow}>
        {activeChat ? (
          <>
            <header className={styles.chatHeader}>
              <div className={styles.chatHeaderIcon}>
                {getMessengerType(activeChat.messenger_id) === 'tg' && <img src={tgLogo} alt="tg"/>}
                {getMessengerType(activeChat.messenger_id) === 'max' && <img src={maxLogo} alt="max"/>}
                {getMessengerType(activeChat.messenger_id) === 'vk' && <img src={vkLogo} alt="vk"/>}
              </div>
              <h2>Чат {activeChat.chat_id_in_messenger}</h2>
            </header>

            <div className={styles.messagesContainer}>
              {messages.filter(msg => msg.chat_id === activeChatId).length > 0 ? (
                messages
                  .filter(msg => msg.chat_id === activeChatId)
                  // Сортируем: старые вверху, новые внизу
                  .sort((a, b) => new Date(a.date) - new Date(b.date))
                  .map((msg) => (
                    <div key={msg.message_id_in_chat} className={styles.messageBubble}>
                      <div className={styles.messageSender}>
                        {(msg.fromuser !== "unnamed") ? msg.fromuser : "Пользователь"}
                      </div>
                      <div className={styles.messageText}>{msg.text}</div>
                      {/* Опционально: можно вывести красиво время */}
                      {messageTime(msg)}
                    </div>
                  ))
              ) : (
                <div className={styles.noMessages}>
                  История сообщений пуста. Напишите что-нибудь!
                </div>
              )}
              {/* Этот пустой див нужен для автоскролла, о нем ниже */}
              <div ref={messagesEndRef} />
            </div>
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