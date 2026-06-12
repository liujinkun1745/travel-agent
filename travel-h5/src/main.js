import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/common.css'

// Vant 组件 & 样式（全局注册，auto-import 在 Vant 4.9.x 存在兼容问题）
import 'vant/lib/index.css'
import { Button } from 'vant'
import { Cell, CellGroup } from 'vant'
import { Collapse, CollapseItem } from 'vant'
import { Dialog } from 'vant'
import { Empty } from 'vant'
import { Field } from 'vant'
import { Icon } from 'vant'
import { Image } from 'vant'
import { Loading } from 'vant'
import { NavBar } from 'vant'
import { Picker } from 'vant'
import { Popup } from 'vant'
import { Tag } from 'vant'
import { Tabbar, TabbarItem } from 'vant'
import { ActionSheet } from 'vant'
import { Overlay } from 'vant'
import { Search } from 'vant'

const app = createApp(App)

app.component(Button.name, Button)
app.component(Cell.name, Cell)
app.component(CellGroup.name, CellGroup)
app.component(Collapse.name, Collapse)
app.component(CollapseItem.name, CollapseItem)
app.component(Dialog.name, Dialog)
app.component(Empty.name, Empty)
app.component(Field.name, Field)
app.component(Icon.name, Icon)
app.component(Image.name, Image)
app.component(Loading.name, Loading)
app.component(NavBar.name, NavBar)
app.component(Picker.name, Picker)
app.component(Popup.name, Popup)
app.component(Tag.name, Tag)
app.component(Tabbar.name, Tabbar)
app.component(TabbarItem.name, TabbarItem)
app.component(ActionSheet.name, ActionSheet)
app.component(Overlay.name, Overlay)
app.component(Search.name, Search)

app.use(createPinia())
app.use(router)
app.mount('#app')
