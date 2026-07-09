#ifndef CHAT_H_
#define CHAT_H_
//xgd
#include "std_msgs/msg/bool.hpp"
#include <cctype>
#include <algorithm>
//xgd
#include <iostream>
#include <chrono>
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>
#include "ollama_ros_msgs/srv/chat.hpp"

class  Chat_Node : public rclcpp::Node{
public:
    Chat_Node(const std::string &node_name,
        const rclcpp::NodeOptions &options);
    ~Chat_Node();
    void sendMessage(const std::string& message);
    void voice_words_Callback(const std_msgs::msg::String::SharedPtr msg);
    void response_callback(rclcpp::Client<ollama_ros_msgs::srv::Chat>::SharedFuture future);

private:
    std::string tts_text;
    bool waiting_for_response_ = false;
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr chat_words_pub;
    //xgd
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr follow_cmd_pub;       // ← 加这行
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr voice_words_sub;
    rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr trigger_item_pub;     //xxg
    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr item_result_sub; //xxg
    rclcpp::Client<ollama_ros_msgs::srv::Chat>::SharedPtr client_;
    std::string removeTags(const std::string& input);
    bool check_follow_intent(const std::string& user_text);                  // ← 加这行
    bool check_stop_intent(const std::string& user_text);                    // ← 加这行
    void publishFollow(bool enable, const std::string& reply_text);          //加上此行
    //xgd

};

#endif /* CHAT_H_ */