using UnityEngine;

namespace Project.Core
{
    /// <summary>
    /// 单例基类，继承自 MonoBehaviour。
    /// 提供全局访问点，并支持 DontDestroyOnLoad 确保实例在场景切换时不被销毁。
    /// 线程安全，适配团结引擎 IL2CPP 环境。
    /// </summary>
    /// <typeparam name="T">继承该基类的子类类型。</typeparam>
    public abstract class Singleton : MonoBehaviour where T : Singleton
    {
        private static T _instance;
        private static readonly object _lock = new object();
        private static bool _applicationIsQuitting = false;

        /// <summary>
        /// 获取单例实例。
        /// 如果实例不存在，会自动查找或创建一个新的 GameObject。
        /// </summary>
        public static T Instance
        {
            get
            {
                if (_applicationIsQuitting)
                {
                    Debug.LogWarning($"[Singleton] Instance '{typeof(T)}' already destroyed on application quit. Won't create again - returning null.");
                    return null;
                }

                lock (_lock)
                {
                    if (_instance == null)
                    {
                        // 尝试在场景中查找已存在的实例
                        // 使用 Unity 2022 推荐的 FindFirstObjectByType 替代 FindObjectOfType 以获得更好的性能
                        _instance = FindFirstObjectByType();

                        if (_instance == null)
                        {
                            // 场景中没有实例，创建新的 GameObject
                            var singletonObject = new GameObject($"{typeof(T).Name} (Singleton)");
                            _instance = singletonObject.AddComponent();
                            
                            DontDestroyOnLoad(singletonObject);
                            
                            Debug.Log($"[Singleton] An instance of {typeof(T)} was created with DontDestroyOnLoad.");
                        }
                        else
                        {
                            // 实例已存在于场景中，确保其 DontDestroyOnLoad 状态
                            // 注意：如果对象原本就在场景中，需要手动处理父节点或直接 DontDestroyOnLoad
                            DontDestroyOnLoad(_instance.gameObject);
                            Debug.Log($"[Singleton] Using instance already created: {_instance.gameObject.name}");
                        }
                    }

                    return _instance;
                }
            }
        }

        /// <summary>
        /// 初始化单例逻辑。
        /// 子类如果重写 Awake，必须调用 base.Awake() 以保证单例机制正常工作。
        /// </summary>
        protected virtual void Awake()
        {
            if (_instance == null)
            {
                _instance = (T)this;
                DontDestroyOnLoad(gameObject);
            }
            else if (_instance != this)
            {
                Debug.LogWarning($"[Singleton] Duplicate instance of {typeof(T)} detected on '{gameObject.name}'. Destroying the new one.");
                Destroy(gameObject);
            }
        }

        /// <summary>
        /// 当实例被销毁时调用。
        /// 清理静态引用，防止内存泄漏或空引用异常。
        /// </summary>
        protected virtual void OnDestroy()
        {
            lock (_lock)
            {
                if (_instance == this)
                {
                    _instance = null;
                }
            }
        }

        /// <summary>
        /// 应用程序退出时标记状态，防止在销毁过程中访问实例。
        /// </summary>
        protected virtual void OnApplicationQuit()
        {
            _applicationIsQuitting = true;
        }
    }
}