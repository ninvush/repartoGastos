-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 31-05-2026 a las 16:29:26
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `reparto_gastos`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `debts`
--

CREATE TABLE `debts` (
  `ID` int(11) NOT NULL,
  `FROM_USER` int(11) NOT NULL,
  `TO_USER` int(11) NOT NULL,
  `AMOUNT` decimal(10,2) NOT NULL,
  `GROUP_ID` int(11) NOT NULL,
  `GROUP_NAME` varchar(255) NOT NULL,
  `CREATION_TIME` timestamp NOT NULL DEFAULT current_timestamp(),
  `MODIFICATION_TIME` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `debts`
--

INSERT INTO `debts` (`ID`, `FROM_USER`, `TO_USER`, `AMOUNT`, `GROUP_ID`, `GROUP_NAME`, `CREATION_TIME`, `MODIFICATION_TIME`) VALUES
(33, 1, 8, 320.00, 1, 'Prueba deudas', '2026-05-30 08:52:14', '2026-05-30 08:52:14'),
(34, 1, 13, 500.00, 1, 'Prueba deudas', '2026-05-30 08:52:14', '2026-05-30 08:52:14'),
(35, 8, 13, 180.00, 1, 'Prueba deudas', '2026-05-30 08:52:14', '2026-05-30 08:52:14'),
(36, 18, 8, 320.00, 1, 'Prueba deudas', '2026-05-30 08:52:14', '2026-05-30 08:52:14'),
(37, 18, 13, 500.00, 1, 'Prueba deudas', '2026-05-30 08:52:14', '2026-05-30 08:52:14'),
(46, 10, 8, 72.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56'),
(47, 13, 8, 100.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56'),
(48, 13, 10, 28.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56'),
(49, 14, 8, 100.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56'),
(50, 14, 10, 28.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56'),
(51, 18, 8, 100.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56'),
(52, 18, 10, 28.00, 2, 'Gastos roma', '2026-05-30 08:53:56', '2026-05-30 08:53:56');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `expenses`
--

CREATE TABLE `expenses` (
  `ID` int(11) NOT NULL,
  `GROUP_ID` int(11) NOT NULL,
  `USER_ID` int(11) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `AMOUNT` decimal(10,2) NOT NULL,
  `GOOGLE_API` varchar(255) NOT NULL,
  `EXPENSE_DATE` timestamp NOT NULL DEFAULT current_timestamp(),
  `MODIFICATION_TIME` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `expenses`
--

INSERT INTO `expenses` (`ID`, `GROUP_ID`, `USER_ID`, `NAME`, `AMOUNT`, `GOOGLE_API`, `EXPENSE_DATE`, `MODIFICATION_TIME`) VALUES
(1, 1, 8, 'Prueba gasto 1000', 1280.00, 'algo', '2026-05-30 14:25:00', '2026-05-30 08:52:11'),
(2, 1, 13, 'Prueba gasto 2000', 2000.00, 'algo', '2026-05-30 08:30:00', '2026-05-30 08:52:14'),
(3, 2, 8, 'Taxi', 50.00, 'algo', '2026-05-30 08:52:00', '2026-05-30 08:53:05'),
(4, 2, 8, 'Hotel roma', 450.00, 'algo', '2026-05-30 08:53:00', '2026-05-30 08:53:30'),
(5, 2, 10, 'Coliseo', 140.00, 'algo', '2026-05-30 08:53:00', '2026-05-30 08:53:56');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `expense_shared`
--

CREATE TABLE `expense_shared` (
  `ID` int(11) NOT NULL,
  `EXPENSE_ID` int(11) NOT NULL,
  `USER_ID` int(11) NOT NULL,
  `AMOUNT` decimal(10,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `expense_shared`
--

INSERT INTO `expense_shared` (`ID`, `EXPENSE_ID`, `USER_ID`, `AMOUNT`) VALUES
(29, 1, 18, 320.00),
(30, 1, 1, 320.00),
(31, 1, 13, 320.00),
(32, 1, 8, 320.00),
(33, 2, 18, 500.00),
(34, 2, 1, 500.00),
(35, 2, 13, 500.00),
(36, 2, 8, 500.00),
(37, 3, 18, 10.00),
(38, 3, 13, 10.00),
(39, 3, 10, 10.00),
(40, 3, 14, 10.00),
(41, 3, 8, 10.00),
(42, 4, 18, 90.00),
(43, 4, 13, 90.00),
(44, 4, 10, 90.00),
(45, 4, 14, 90.00),
(46, 4, 8, 90.00),
(47, 5, 18, 28.00),
(48, 5, 13, 28.00),
(49, 5, 10, 28.00),
(50, 5, 14, 28.00),
(51, 5, 8, 28.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `groups`
--

CREATE TABLE `groups` (
  `ID` int(11) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `CREATOR_USER` int(11) NOT NULL,
  `CREATION` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `groups`
--

INSERT INTO `groups` (`ID`, `NAME`, `CREATOR_USER`, `CREATION`) VALUES
(1, 'Prueba deudas', 8, '2026-05-30 08:18:39'),
(2, 'Gastos roma', 8, '2026-05-30 08:52:43');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `group_users`
--

CREATE TABLE `group_users` (
  `ID` int(11) NOT NULL,
  `USER_INVITED` int(11) NOT NULL,
  `INVITE_USER` int(11) NOT NULL,
  `GROUP_ID` int(11) NOT NULL,
  `INVITE_TIME` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `group_users`
--

INSERT INTO `group_users` (`ID`, `USER_INVITED`, `INVITE_USER`, `GROUP_ID`, `INVITE_TIME`) VALUES
(1, 18, 8, 1, '2026-05-30 08:18:39'),
(2, 1, 8, 1, '2026-05-30 08:18:39'),
(3, 13, 8, 1, '2026-05-30 08:18:39'),
(4, 18, 8, 2, '2026-05-30 08:52:43'),
(5, 13, 8, 2, '2026-05-30 08:52:43'),
(6, 10, 8, 2, '2026-05-30 08:52:43'),
(7, 14, 8, 2, '2026-05-30 08:52:43');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `ID` int(11) NOT NULL,
  `NAME` varchar(255) NOT NULL,
  `EMAIL` varchar(255) NOT NULL,
  `PASSWORD` varchar(255) NOT NULL,
  `CREATION` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`ID`, `NAME`, `EMAIL`, `PASSWORD`, `CREATION`) VALUES
(1, 'Carlos', 'carlos@email.com', 'scrypt:32768:8:1$NZvFEolKm5SPOLgR$048bb7d11ca26841a5820e79e8558fbe6031e3ba25b3b94cf5855c3267a4fa9ad1a0587d456831a72192afee9235371dff244b3ac4cbce6f5638d28e667c4bf7', '2026-02-07 16:11:37'),
(2, 'Ana', 'ana@email.com', 'scrypt:32768:8:1$xNguHKmuBxh0LbMn$a4d35678b679e6464109b4b59c01cfd6607afcafa42309e558f6ff2e9ef8de5df42e9692fa8ace14154c7051b408016f3205740f98a6e90e9e90c8bf717576e8', '2026-02-07 16:11:37'),
(3, 'Juan', 'juan@email.com', 'scrypt:32768:8:1$whf4R9kUYRQafM63$03d3049c0664f5315a2c60ff71d62af34ce94f9ec9ef6f04bd11c40c4a4a91d397d915781e266dac25ad8007b77abfa85c0bd56ad005f037d7bef8eb21e3211a', '2026-02-07 16:11:37'),
(4, 'Laura', 'laura@email.com', 'scrypt:32768:8:1$s5uqtAbMJsHyilr4$19df1577ea9907e1dc212fda302534a3752b0e8b6859a47d482e7edfc648aaf850916a8a283df5c5e69497f1366bb6a6a851fc6185e5f8e24573f2a98f7de974', '2026-02-07 16:11:37'),
(5, 'Marta', 'marta@email.com', 'scrypt:32768:8:1$Ue9iLHNg7BOGselD$315cdc1a8ddb6a99973f1c1c8f4d2f0387069666dd75acdfac026d9f4334bd20b8a83d4684cbd629b7689e3f26dbb59736197129d045734821f4c7ef3a193999', '2026-05-02 16:20:00'),
(6, 'Pedro', 'pedro@email.com', 'scrypt:32768:8:1$oENO1Ddo8EqRWZlm$680801f6da36578db31392949a037b1b6b02f4b21ba6a00df6d3dec58c9768d800d8f077599ada459376604cdc8765581fe9091a8740e0df4debcc527a130fb7', '2026-05-02 16:21:00'),
(7, 'Lucía', 'lucia@email.com', 'scrypt:32768:8:1$IwwwCPTAvN01U4Jd$1e115a828e6b30e7214f4540f712352f2da8623acee8dca8245391e517ce480e6abeb89bb2f6d3fbfde709642e27cb2542ac968290990629f5393043345deb1d', '2026-05-02 16:22:00'),
(8, 'Sergio', 'sergio@email.com', 'scrypt:32768:8:1$NCPmtZJTc4RKkEG0$aac4af574393a5734df55ac09821789c8e1576882e4e26382c6431c5b36df81ba7156b1fc1a1cc76535897649bb7e7f5bc43dd2519cdd0e2593a955ff5d2c0aa', '2026-05-02 16:23:00'),
(9, 'Nerea', 'nerea@email.com', 'scrypt:32768:8:1$nfA1wjGQ3IcMaR2O$6c29923a4fd9ac2662ca6b92521c14d11c23c81366257fa0c01ae4d942bf2511bdfdda640ad666823d70028e3e6a0d152b5e234c400a9b8bce9ae6f1f79d9e72', '2026-05-02 16:24:00'),
(10, 'David', 'david@email.com', 'scrypt:32768:8:1$qqHCelGM64rJPgUm$414bf4fbe87995e19b8e2c54873c3ca7545110175b03f767ed98aacb23e68c1e002e5774207de1d959c233014b687a3c55ffabafce5cd50bf186d6112925affa', '2026-05-02 16:25:00'),
(11, 'Elena', 'elena@email.com', 'scrypt:32768:8:1$8NpR39qx6UtWRBWQ$451e7dc792e1969b8ffb0b6c6753feec82e6e2d70f0ec8408ce5ffcc67bf77971ed1dad2312eb4f858cbe4cd16bc488be2580025225cdfa468e74409c457c775', '2026-05-02 16:26:00'),
(12, 'Mario', 'mario@email.com', 'scrypt:32768:8:1$JADFcGTuzxIePvM8$ecb68e94dc51d20a5835493a157418a4ba91cdcc25aba864011b67f3b004a466d1747fd92ffafb322dbd66fb27fa3899d695ee1120ca55b6fdb8bb1fc4858785', '2026-05-02 16:27:00'),
(13, 'Claudia', 'claudia@email.com', 'scrypt:32768:8:1$5Zq9bBIJ58ZdQwUr$082163408dc14959414f4ab03f7345f7dfbb3de6d8631d8df7280148e109ae5f8191464ad904423760a16d9f9528139d01160abd0334e0dd07606b0ea4aee200', '2026-05-02 16:28:00'),
(14, 'Hugo', 'hugo@email.com', 'scrypt:32768:8:1$gmUPq9OorLejisW9$e8003bccc2c6c33fbd8f98cc41b66f2bd3b8736aa138af2542512d913e97faad0e7e929f5275fa5e94ae4a69d467b4bb752b7199c4494c3bcccdec8c311d76c8', '2026-05-02 16:29:00'),
(15, 'Paula', 'paula@email.com', 'scrypt:32768:8:1$EjEZaXKanCUmLjUX$f2bf8c67c973999da548ac5e23f03a1fb1d4d17caf40a5bb994aee00b846dbcfe096afd01d5690d0a24967a2c5bc1035321df1c9b0873526ca5398c69cb85764', '2026-05-02 16:30:00'),
(16, 'Javier', 'javier@email.com', 'scrypt:32768:8:1$MxQlbiwpLvuh7DxU$fba2f9e4facf46412c62aaf62644c0857158a15df05fbef72325c7a50bcc73f00bd22a2714cb0a64279b867627724ad5fc87e548c06fe9cde796083547a72f86', '2026-05-02 16:31:00'),
(17, 'Irene', 'irene@email.com', 'scrypt:32768:8:1$VIEBKXwXQokvQoQP$2f43ec053c76a761f04a3ace7327913fefcec12e7f3bd0f53ee25084f0bee9ab71927411b29135a3d273a438528d0bbe60936601c17be871eb07e08cbbebb873', '2026-05-02 16:32:00'),
(18, 'Álvaro', 'alvaro@email.com', 'scrypt:32768:8:1$oIRGDvv6fQeqME8Y$c8af621156abb956e62419f56d862ab8177b78deaae60f0dc90ba7424316b644aa380f4102af7765089115dde625dc15e1eb415b4afaeb4af724ab9886d5a762', '2026-05-02 16:33:00'),
(19, 'Noelia', 'noelia@email.com', 'scrypt:32768:8:1$XseAS3bRPOR5XFzH$4e244d159da357db3b0862b26748b3a71dc3b1745fc2c36219f3fb85197a5a0d871871b00606a1af9e14b0f957b83aa85e44849c5bad497ddf37f0cd19f636bb', '2026-05-02 16:34:00'),
(20, 'Raúl', 'raul@email.com', 'scrypt:32768:8:1$Asnq37DW4JBTi1cd$f33889cd9606ce95de69f0eff8654de0a7f51538f8db5ef831af42881121fdafe5b26b04c4e52f6d280b3a1ae63a68f44943a9b631aae813476703f5726147ac', '2026-05-02 16:35:00'),
(21, 'Pepe', 'pepemaster@hotmail.com', 'scrypt:32768:8:1$JtLyn0bD45fQ8FPu$22204f90044d9909b1c425dcbb6fa3c20afe84e0f7823fd174306d7e70e2fe2278f4ee6741e5b8292b842ffb11b2d8f196d3cc7b290539fac1ed5b30ea7266b4', '2026-05-24 15:28:43'),
(22, 'Ejemplo2', 'ejemplo4@gmail.com', 'scrypt:32768:8:1$ndFDUQ85jzsHAVoR$37e8c2b7394e705cc6f75ab9140b43e3fdb7bd70ad83f62b177a57b70e362c13f07a3f79c6bb2fb52cc2c9d7bc3008c192ae7344376071b118f529f0c01d9397', '2026-05-24 15:36:23'),
(23, 'Beckam', 'davidelbecario@hotmail.com', 'scrypt:32768:8:1$4oHst1zhGvWctynA$c95f337e8c0f0f2018563e0c820d4523706bac164e211e44f4a5b9cd052960679f0ce855857bd3e48918ae9b80bc4c974009be4bdb8cf4394162c317bd508956', '2026-05-24 16:12:21');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `debts`
--
ALTER TABLE `debts`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `FROM_USER` (`FROM_USER`),
  ADD KEY `TO_USER` (`TO_USER`);

--
-- Indices de la tabla `expenses`
--
ALTER TABLE `expenses`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `GROUP_ID` (`GROUP_ID`),
  ADD KEY `USER_ID` (`USER_ID`);

--
-- Indices de la tabla `expense_shared`
--
ALTER TABLE `expense_shared`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `EXPENSE_ID` (`EXPENSE_ID`),
  ADD KEY `USER_ID` (`USER_ID`);

--
-- Indices de la tabla `groups`
--
ALTER TABLE `groups`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `CREATOR_USER` (`CREATOR_USER`);

--
-- Indices de la tabla `group_users`
--
ALTER TABLE `group_users`
  ADD PRIMARY KEY (`ID`),
  ADD KEY `USER_INVITED` (`USER_INVITED`),
  ADD KEY `INVITE_USER` (`INVITE_USER`),
  ADD KEY `GROUP_ID` (`GROUP_ID`);

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`ID`),
  ADD UNIQUE KEY `EMAIL` (`EMAIL`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `debts`
--
ALTER TABLE `debts`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

--
-- AUTO_INCREMENT de la tabla `expenses`
--
ALTER TABLE `expenses`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `expense_shared`
--
ALTER TABLE `expense_shared`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=52;

--
-- AUTO_INCREMENT de la tabla `groups`
--
ALTER TABLE `groups`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `group_users`
--
ALTER TABLE `group_users`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `users`
--
ALTER TABLE `users`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `debts`
--
ALTER TABLE `debts`
  ADD CONSTRAINT `debts_ibfk_1` FOREIGN KEY (`FROM_USER`) REFERENCES `users` (`ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `debts_ibfk_2` FOREIGN KEY (`TO_USER`) REFERENCES `users` (`ID`) ON DELETE CASCADE;

--
-- Filtros para la tabla `expenses`
--
ALTER TABLE `expenses`
  ADD CONSTRAINT `expenses_ibfk_1` FOREIGN KEY (`GROUP_ID`) REFERENCES `groups` (`ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `expenses_ibfk_2` FOREIGN KEY (`USER_ID`) REFERENCES `users` (`ID`) ON DELETE CASCADE;

--
-- Filtros para la tabla `expense_shared`
--
ALTER TABLE `expense_shared`
  ADD CONSTRAINT `expense_shared_ibfk_1` FOREIGN KEY (`EXPENSE_ID`) REFERENCES `expenses` (`ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `expense_shared_ibfk_2` FOREIGN KEY (`USER_ID`) REFERENCES `users` (`ID`) ON DELETE CASCADE;

--
-- Filtros para la tabla `groups`
--
ALTER TABLE `groups`
  ADD CONSTRAINT `groups_ibfk_1` FOREIGN KEY (`CREATOR_USER`) REFERENCES `users` (`ID`) ON DELETE CASCADE;

--
-- Filtros para la tabla `group_users`
--
ALTER TABLE `group_users`
  ADD CONSTRAINT `group_users_ibfk_1` FOREIGN KEY (`USER_INVITED`) REFERENCES `users` (`ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `group_users_ibfk_2` FOREIGN KEY (`INVITE_USER`) REFERENCES `users` (`ID`) ON DELETE CASCADE,
  ADD CONSTRAINT `group_users_ibfk_3` FOREIGN KEY (`GROUP_ID`) REFERENCES `groups` (`ID`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
