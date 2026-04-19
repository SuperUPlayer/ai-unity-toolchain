using UnityEngine;
public class Sample : MonoBehaviour
{
    void Update()
    {
        var rb = GetComponent<Rigidbody>();
        Debug.Log("Pos: " + transform.position.ToString());
    }
}